import unittest
from unittest.mock import Mock

from app.epic.client import EpicFHIRClient, FHIRAuthorizationExpiredError, FHIRPermissionError
from app.main import app


class EpicFHIRClientTests(unittest.TestCase):
    def test_search_excludes_operation_outcomes_from_requested_resources(self):
        client = EpicFHIRClient("https://example.test/fhir", "not-a-real-token")
        response = Mock()
        response.json.return_value = {
            "entry": [
                {"resource": {"resourceType": "DiagnosticReport", "id": "report-1"}},
                {"resource": {"resourceType": "OperationOutcome", "issue": []}},
            ]
        }
        response.raise_for_status.return_value = None
        client.session.get = Mock(return_value=response)

        reports = list(client.search("DiagnosticReport", {"patient": "patient-1"}))

        self.assertEqual(reports, [{"resourceType": "DiagnosticReport", "id": "report-1"}])

    def test_search_raises_safe_error_for_forbidden_resource(self):
        client = EpicFHIRClient("https://example.test/fhir", "not-a-real-token")
        response = Mock(status_code=403)
        client.session.get = Mock(return_value=response)
        with self.assertRaises(FHIRPermissionError):
            list(client.search("Condition", {"patient": "patient-1"}))

    def test_search_raises_safe_error_for_expired_authorization(self):
        client = EpicFHIRClient("https://example.test/fhir", "not-a-real-token")
        response = Mock(status_code=401)
        client.session.get = Mock(return_value=response)
        with self.assertRaises(FHIRAuthorizationExpiredError):
            list(client.search("Observation", {"patient": "patient-1"}))

    def test_data_requires_authorization_without_scope_error(self):
        import app.main as main
        previous_token = main.token_response
        main.token_response = None
        try:
            response = app.test_client().get("/data")
            self.assertEqual(response.status_code, 401)
        finally:
            main.token_response = previous_token
