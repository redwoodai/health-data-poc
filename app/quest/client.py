class QuestPatientAccessUnavailable(RuntimeError):
    """Raised instead of attempting unsupported MyQuest access."""


class QuestClient:
    """Deliberately non-functional until Quest offers a documented consumer API contract."""

    def fetch_patient_results(self) -> None:
        raise QuestPatientAccessUnavailable(
            "No verified official Quest patient-authorized results API is configured for this PoC. "
            "This project will not scrape MyQuest or use private endpoints."
        )
