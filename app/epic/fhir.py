from __future__ import annotations

import logging
from typing import Any

from app.models.normalized import ClinicalItem, LabResult, NormalizedPatient, NormalizedPayload

logger = logging.getLogger(__name__)

def _display(value: dict[str, Any] | None) -> str | None:
    if not value:
        return None
    return value.get("text") or next((item.get("display") for item in value.get("coding", []) if item.get("display")), None)


def normalize_patient(resource: dict[str, Any]) -> NormalizedPatient:
    name = next(iter(resource.get("name", [])), {})
    return NormalizedPatient(
        source_resource_id=resource["id"],
        name=" ".join(name.get("given", []) + ([name["family"]] if name.get("family") else [])).strip() or None,
        birth_date=resource.get("birthDate"),
        gender=resource.get("gender"),
    )


def normalize_labs(observations: list[dict[str, Any]]) -> list[LabResult]:
    labs: list[LabResult] = []
    for observation in observations:
        resource_id = observation.get("id")
        if not resource_id:
            # A source response can be incomplete or non-conformant. Do not
            # manufacture an identifier; preserving provenance is required for
            # normalized results. The log intentionally contains no resource data.
            logger.warning("Skipping an Observation without a FHIR resource ID")
            continue
        value_quantity = observation.get("valueQuantity", {})
        value: str | int | float | None = value_quantity.get("value")
        if value is None:
            value = observation.get("valueString") or _display(observation.get("valueCodeableConcept"))
        reference = observation.get("referenceRange", [])
        reference_text = reference[0].get("text") if reference else None
        if not reference_text and reference:
            low, high = reference[0].get("low", {}).get("value"), reference[0].get("high", {}).get("value")
            reference_text = f"{low if low is not None else ''}-{high if high is not None else ''}".strip("-") or None
        labs.append(LabResult(
            name=_display(observation.get("code")) or "Unnamed laboratory observation",
            value=value,
            unit=value_quantity.get("unit"),
            date=observation.get("effectiveDateTime") or observation.get("issued"),
            reference_range=reference_text,
            source_resource_id=resource_id,
        ))
    return labs


def _clinical_items(resources: list[dict[str, Any]], code_key: str, detail) -> list[ClinicalItem]:
    items: list[ClinicalItem] = []
    for resource in resources:
        resource_id = resource.get("id")
        if not resource_id:
            logger.warning("Skipping a clinical resource without a FHIR resource ID")
            continue
        items.append(ClinicalItem(
            name=_display(resource.get(code_key)) or "Adı belirtilmemiş kayıt",
            status=_display(resource.get("clinicalStatus")) or resource.get("status"),
            detail=detail(resource),
            source_resource_id=resource_id,
        ))
    return items


def normalize_conditions(resources: list[dict[str, Any]]) -> list[ClinicalItem]:
    return _clinical_items(resources, "code", lambda r: _display(r.get("verificationStatus")))


def normalize_allergies(resources: list[dict[str, Any]]) -> list[ClinicalItem]:
    return _clinical_items(resources, "code", lambda r: r.get("criticality"))


def normalize_medications(resources: list[dict[str, Any]]) -> list[ClinicalItem]:
    return _clinical_items(resources, "medicationCodeableConcept", lambda r: r.get("dosageInstruction", [{}])[0].get("text"))


def normalized_payload(patient: dict[str, Any], observations: list[dict[str, Any]], diagnostic_reports: list[dict[str, Any]], conditions: list[dict[str, Any]] | None = None, allergies: list[dict[str, Any]] | None = None, medications: list[dict[str, Any]] | None = None, extended_clinical_data_enabled: bool = False, unavailable_sections: list[str] | None = None) -> NormalizedPayload:
    # Raw FHIR resources are intentionally not attached to the provider-neutral
    # output model or returned by /data. A product can later persist them in a
    # separately protected raw-data layer if the user explicitly chooses that.
    return NormalizedPayload(
        source="epic",
        patient=normalize_patient(patient),
        labs=normalize_labs(observations),
        diagnostic_report_count=len(diagnostic_reports),
        conditions=normalize_conditions(conditions or []),
        allergies=normalize_allergies(allergies or []),
        medications=normalize_medications(medications or []),
        extended_clinical_data_enabled=extended_clinical_data_enabled,
        unavailable_sections=unavailable_sections or [],
    )
