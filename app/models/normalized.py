from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizedPatient:
    source_resource_id: str
    name: str | None
    birth_date: str | None
    gender: str | None


@dataclass(frozen=True)
class LabResult:
    name: str
    value: str | int | float | None
    unit: str | None
    date: str | None
    reference_range: str | None
    source_resource_id: str


@dataclass(frozen=True)
class ClinicalItem:
    name: str
    status: str | None
    detail: str | None
    source_resource_id: str


@dataclass(frozen=True)
class NormalizedPayload:
    source: str
    patient: NormalizedPatient
    labs: list[LabResult]
    diagnostic_report_count: int
    conditions: list[ClinicalItem]
    allergies: list[ClinicalItem]
    medications: list[ClinicalItem]
    extended_clinical_data_enabled: bool
    unavailable_sections: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
