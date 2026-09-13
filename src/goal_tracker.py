from src.evidence_builder import EvidenceBuilder


class GoalTracker:
    REQUIRED_GOALS = {
        "company_overview",
        "target_audience",
        "contact_information",
        "leadership",
    }

    def __init__(self):
        self.evidence_builder = EvidenceBuilder()

    def find_missing(self, collected_pages):
        completed = self.evidence_builder.completed_goals(collected_pages)
        return self.REQUIRED_GOALS - completed
