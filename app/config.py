from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv


DEFAULT_SCOPES = (
    "launch/patient openid fhirUser "
    "patient/Patient.r "
    "patient/Observation.rs patient/DiagnosticReport.rs"
)
EXTENDED_CLINICAL_SCOPES = (
    " patient/Condition.rs patient/AllergyIntolerance.rs patient/MedicationRequest.rs"
)


@dataclass(frozen=True)
class Settings:
    fhir_base_url: str
    client_id: str
    redirect_uri: str
    client_secret: str | None
    scopes: str
    host: str
    port: int
    enable_extended_clinical_data: bool

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        fhir_base_url = os.getenv("EPIC_FHIR_BASE_URL", "").rstrip("/")
        client_id = os.getenv("EPIC_CLIENT_ID", "")
        redirect_uri = os.getenv("EPIC_REDIRECT_URI", "http://127.0.0.1:8000/callback")
        if not fhir_base_url or not client_id:
            raise ValueError("EPIC_FHIR_BASE_URL and EPIC_CLIENT_ID must be set in .env")
        parsed = urlparse(redirect_uri)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("This PoC permits only an http localhost callback")
        enabled = os.getenv("EPIC_ENABLE_EXTENDED_CLINICAL_DATA", "false").lower() in {"1", "true", "yes"}
        scopes = os.getenv("EPIC_SCOPES") or DEFAULT_SCOPES
        if enabled:
            scopes += EXTENDED_CLINICAL_SCOPES
        return cls(
            fhir_base_url=fhir_base_url,
            client_id=client_id,
            redirect_uri=redirect_uri,
            client_secret=os.getenv("EPIC_CLIENT_SECRET") or None,
            scopes=scopes,
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8000")),
            enable_extended_clinical_data=enabled,
        )
