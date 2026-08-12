import unittest

from app.epic.fhir import normalize_labs, normalize_patient, normalized_payload


class FhirNormalizationTests(unittest.TestCase):
    def test_normalizes_patient_and_lab_without_raw_resource_mix(self):
        patient = normalize_patient({"id": "p1", "name": [{"given": ["Ada"], "family": "Lovelace"}], "birthDate": "1815-12-10", "gender": "female"})
        labs = normalize_labs([{
            "id": "obs1", "code": {"coding": [{"display": "LDL Cholesterol"}]},
            "valueQuantity": {"value": 120, "unit": "mg/dL"}, "effectiveDateTime": "2026-01-01",
            "referenceRange": [{"text": "<100 mg/dL"}],
        }])
        self.assertEqual(patient.name, "Ada Lovelace")
        self.assertEqual(labs[0].name, "LDL Cholesterol")
        self.assertEqual(labs[0].value, 120)
        self.assertEqual(labs[0].reference_range, "<100 mg/dL")

    def test_skips_observation_without_a_resource_id(self):
        labs = normalize_labs([{"code": {"text": "Incomplete result"}}])
        self.assertEqual(labs, [])

    def test_normalized_payload_does_not_include_raw_diagnostic_reports(self):
        payload = normalized_payload(
            {"id": "p1"}, [], [{"resourceType": "DiagnosticReport", "id": "report-1"}]
        ).to_dict()
        self.assertEqual(payload["diagnostic_report_count"], 1)
        self.assertNotIn("diagnostic_reports", payload)
        self.assertFalse(payload["extended_clinical_data_enabled"])
        self.assertEqual(payload["unavailable_sections"], [])

    def test_normalizes_extended_clinical_data(self):
        payload = normalized_payload(
            {"id": "p1"}, [], [],
            conditions=[{"id": "c1", "code": {"text": "Hypertension"}, "clinicalStatus": {"text": "active"}}],
            allergies=[{"id": "a1", "code": {"text": "Penicillin"}, "criticality": "high"}],
            medications=[{"id": "m1", "medicationCodeableConcept": {"text": "Metformin"}, "status": "active", "dosageInstruction": [{"text": "Daily"}]}],
            extended_clinical_data_enabled=True,
        ).to_dict()
        self.assertEqual(payload["conditions"][0]["name"], "Hypertension")
        self.assertEqual(payload["allergies"][0]["detail"], "high")
        self.assertEqual(payload["medications"][0]["detail"], "Daily")
        self.assertTrue(payload["extended_clinical_data_enabled"])
