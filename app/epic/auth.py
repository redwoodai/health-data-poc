from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SmartMetadata:
    authorization_endpoint: str
    token_endpoint: str
    code_challenge_methods_supported: tuple[str, ...]


@dataclass(frozen=True)
class AuthorizationRequest:
    url: str
    state: str
    code_verifier: str


class SmartAuth:
    def __init__(self, fhir_base_url: str, client_id: str, redirect_uri: str, scopes: str, client_secret: str | None = None):
        self.fhir_base_url = fhir_base_url.rstrip("/")
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.client_secret = client_secret

    def discover(self) -> SmartMetadata:
        # SMART metadata is defined relative to the FHIR base URL.
        response = requests.get(f"{self.fhir_base_url}/.well-known/smart-configuration", timeout=15)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        try:
            return SmartMetadata(
                authorization_endpoint=data["authorization_endpoint"],
                token_endpoint=data["token_endpoint"],
                code_challenge_methods_supported=tuple(data.get("code_challenge_methods_supported", [])),
            )
        except KeyError as exc:
            raise ValueError("SMART configuration omitted a required endpoint") from exc

    @staticmethod
    def _pkce_pair() -> tuple[str, str]:
        verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return verifier, challenge

    def build_authorization_request(self, metadata: SmartMetadata) -> AuthorizationRequest:
        if "S256" not in metadata.code_challenge_methods_supported:
            raise ValueError("The selected SMART server does not advertise S256 PKCE support")
        verifier, challenge = self._pkce_pair()
        state = secrets.token_urlsafe(32)
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            # SMART v2 binds the authorization request to the intended FHIR
            # resource server. Epic's R4 registration can be configured for v2.
            "aud": self.fhir_base_url,
            "scope": self.scopes,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        return AuthorizationRequest(f"{metadata.authorization_endpoint}?{urlencode(params)}", state, verifier)

    def exchange_code(self, metadata: SmartMetadata, code: str, code_verifier: str) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        }
        auth = (self.client_id, self.client_secret) if self.client_secret else None
        # A confidential registration may require its configured client authentication;
        # a public client sends client_id in the form body and uses PKCE.
        response = requests.post(metadata.token_endpoint, data=data, auth=auth, timeout=15)
        response.raise_for_status()
        token: dict[str, Any] = response.json()
        if "access_token" not in token or "patient" not in token:
            raise ValueError("Token response did not include an access token and patient context")
        logger.info("SMART authorization completed; token and patient context are retained only in memory")
        return token
