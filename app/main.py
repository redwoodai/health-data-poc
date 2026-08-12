from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from flask import Flask, abort, redirect, request, Response, render_template

from app.config import Settings
from app.epic.auth import SmartAuth
from app.epic.client import EpicFHIRClient, FHIRAuthorizationExpiredError, FHIRPermissionError
from app.epic.fhir import normalized_payload

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
# Werkzeug's development access log includes request query strings. OAuth
# callbacks carry one-time authorization codes in that string, so do not log
# routine HTTP requests in this PoC.
logging.getLogger("werkzeug").setLevel(logging.WARNING)
app = Flask(__name__)


@dataclass
class PendingAuthorization:
    state: str
    code_verifier: str


pending: PendingAuthorization | None = None
# Deliberately process-memory only. Never serialize this token or log it.
token_response: dict | None = None


def _settings() -> Settings:
    return Settings.from_env()


@app.get("/")
def index() -> str:
    return render_template("index.html", authorized=token_response is not None)


@app.get("/authorize")
def authorize():
    global pending
    settings = _settings()
    auth = SmartAuth(settings.fhir_base_url, settings.client_id, settings.redirect_uri, settings.scopes, settings.client_secret)
    request_data = auth.build_authorization_request(auth.discover())
    pending = PendingAuthorization(request_data.state, request_data.code_verifier)
    logger.info("Redirecting to Epic authorization endpoint")
    return redirect(request_data.url)


@app.get("/callback")
def callback():
    global token_response, pending
    if request.args.get("error"):
        logger.warning("Authorization was denied or failed: %s", request.args.get("error"))
        abort(400, "Authorization was denied or failed. See local log for non-sensitive error code.")
    if not pending or request.args.get("state") != pending.state or not request.args.get("code"):
        logger.warning("Rejected callback with missing or mismatched state")
        abort(400, "Invalid authorization callback state")
    settings = _settings()
    auth = SmartAuth(settings.fhir_base_url, settings.client_id, settings.redirect_uri, settings.scopes, settings.client_secret)
    token_response = auth.exchange_code(auth.discover(), request.args["code"], pending.code_verifier)
    pending = None
    return redirect("/dashboard")


@app.get("/data")
def data() -> Response:
    if not token_response:
        abort(401, "Authorize first at /authorize")
    settings = _settings()
    client = EpicFHIRClient(settings.fhir_base_url, token_response["access_token"])
    patient_id = token_response["patient"]
    try:
        patient = client.get_resource("Patient", patient_id)
        observations = list(client.search("Observation", {"patient": patient_id, "category": "laboratory", "_count": "100"}))
        reports = list(client.search("DiagnosticReport", {"patient": patient_id, "category": "LAB", "_count": "100"}))
    except FHIRAuthorizationExpiredError:
        token_response = None
        logger.info("Epic authorization expired; a new authorization is required")
        return Response(json.dumps({"error": "authorization_expired", "reauthorize_url": "/authorize"}), status=401, mimetype="application/json")
    conditions = allergies = medications = []
    unavailable_sections: list[str] = []
    if settings.enable_extended_clinical_data:
        optional_searches = {
            "conditions": ("Condition", {"patient": patient_id, "category": "problem-list-item", "_count": "100"}),
            "allergies": ("AllergyIntolerance", {"patient": patient_id, "_count": "100"}),
            "medications": ("MedicationRequest", {"patient": patient_id, "_count": "100"}),
        }
        for section, (resource_type, params) in optional_searches.items():
            try:
                results = list(client.search(resource_type, params))
                if section == "conditions": conditions = results
                elif section == "allergies": allergies = results
                else: medications = results
            except FHIRPermissionError:
                unavailable_sections.append(section)
                logger.warning("Optional clinical section unavailable because it was not authorized: %s", section)
    payload = normalized_payload(patient, observations, reports, conditions, allergies, medications, settings.enable_extended_clinical_data, unavailable_sections)
    logger.info("Retrieved and normalized Epic data")
    return Response(json.dumps(payload.to_dict(), indent=2), mimetype="application/json")


@app.get("/dashboard")
def dashboard() -> str:
    if not token_response:
        return redirect("/authorize")
    return render_template("dashboard.html", granted_scopes=token_response.get("scope", "").split())


if __name__ == "__main__":
    settings = _settings()
    app.run(host=settings.host, port=settings.port, debug=False)
