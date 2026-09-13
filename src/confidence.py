from src.evidence_pack import EvidencePack
from src.models import LeadProfileDraft


class ConfidenceEngine:
    FIELD_WEIGHTS = {
        "company_overview": 0.25,
        "icp": 0.25,
        "generic_emails": 0.20,
        "leadership": 0.20,
    }

    def calculate(
        self,
        profile: LeadProfileDraft,
        evidence: EvidencePack,
    ) -> float:
        score = 0.0

        evidence_fields = {
            item.field
            for item in evidence.items
            if item.value.strip()
        }

        if profile.company_overview.strip() and "company_overview" in evidence_fields:
            score += self.FIELD_WEIGHTS["company_overview"]

        if profile.icp.strip() and (
            "target_audience" in evidence_fields
            or "icp" in evidence_fields
        ):
            score += self.FIELD_WEIGHTS["icp"]

        if profile.generic_emails and "contact_information" in evidence_fields:
            score += self.FIELD_WEIGHTS["generic_emails"]

        if profile.leadership and "leadership" in evidence_fields:
            score += self.FIELD_WEIGHTS["leadership"]

        if evidence.items:
            score += 0.10

        return round(min(score, 1.0), 2)