from __future__ import annotations

import logging
from typing import Any, Iterator

import requests

logger = logging.getLogger(__name__)


class FHIRPermissionError(RuntimeError):
    """The current authorization did not grant access to an optional resource."""


class FHIRAuthorizationExpiredError(RuntimeError):
    """The authorization is absent, expired, or otherwise no longer usable."""


class EpicFHIRClient:
    def __init__(self, fhir_base_url: str, access_token: str):
        self.fhir_base_url = fhir_base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {access_token}", "Accept": "application/fhir+json"})

    def get_resource(self, resource_type: str, resource_id: str) -> dict[str, Any]:
        response = self.session.get(f"{self.fhir_base_url}/{resource_type}/{resource_id}", timeout=20)
        if response.status_code == 401:
            raise FHIRAuthorizationExpiredError("Epic authorization is no longer valid")
        response.raise_for_status()
        return response.json()

    def search(self, resource_type: str, params: dict[str, str], max_pages: int = 10) -> Iterator[dict[str, Any]]:
        url = f"{self.fhir_base_url}/{resource_type}"
        for _ in range(max_pages):
            response = self.session.get(url, params=params if url.endswith(resource_type) else None, timeout=20)
            if response.status_code == 401:
                raise FHIRAuthorizationExpiredError("Epic authorization is no longer valid")
            if response.status_code == 403:
                raise FHIRPermissionError(f"Access was not granted for {resource_type}")
            response.raise_for_status()
            bundle = response.json()
            for entry in bundle.get("entry", []):
                resource = entry.get("resource")
                if resource and resource.get("resourceType") == resource_type:
                    yield resource
                elif resource and resource.get("resourceType") == "OperationOutcome":
                    # Epic can include a non-fatal warning alongside a search
                    # result Bundle. It is not a resource of the requested type.
                    logger.warning("FHIR search returned a non-fatal OperationOutcome warning")
                elif resource:
                    logger.warning("FHIR search returned an unexpected resource type; skipping it")
            next_links = [link["url"] for link in bundle.get("link", []) if link.get("relation") == "next" and link.get("url")]
            if not next_links:
                return
            url, params = next_links[0], {}
