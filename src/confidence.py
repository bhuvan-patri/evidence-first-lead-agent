from src.evidence_pack import EvidencePack
from src.models import LeadProfileDraft


class ConfidenceEngine:
    FIELD_WEIGHTS = {
        "company_overview": 0.25,
        "icp": 0.25,
        "generic_emails": 0.20,
        "leadership": 0.20,
    }
    STRENGTH_MULTIPLIERS = {
        "strong": 1.0,
        "medium": 0.70,
        "weak": 0.0,
    }
    FIRST_PARTY_COMPLETENESS_BONUS = 0.05
    CORROBORATION_BONUS_PER_FIELD = 0.01
    MAX_CORROBORATION_BONUS = 0.05

    def calculate(
        self,
        profile: LeadProfileDraft,
        evidence: EvidencePack,
    ) -> float:
        score = 0.0

        field_items = {
            "company_overview": self._items_for(evidence, "company_overview"),
            "icp": self._items_for(evidence, "target_audience", "icp"),
            "generic_emails": self._items_for(evidence, "contact_information"),
            "leadership": self._items_for(evidence, "leadership"),
        }
        populated = {
            "company_overview": bool(profile.company_overview.strip()),
            "icp": bool(profile.icp.strip()),
            "generic_emails": bool(profile.generic_emails),
            "leadership": bool(profile.leadership),
        }

        for field, is_populated in populated.items():
            if not is_populated or not field_items[field]:
                continue
            strength = max(
                self.STRENGTH_MULTIPLIERS.get(item.strength, 0.0)
                for item in field_items[field]
            )
            quality = strength
            if field == "leadership" and not any(person.linkedin_url for person in profile.leadership):
                # Names and roles are useful, but a verified public profile
                # provides an additional identity check for a lead record.
                quality *= 0.85
            score += self.FIELD_WEIGHTS[field] * quality

        supported_fields = [field for field in populated if populated[field] and field_items[field]]
        if supported_fields and all(
            any(item.source_type == "company_website" for item in field_items[field])
            for field in supported_fields
        ):
            score += self.FIRST_PARTY_COMPLETENESS_BONUS

        corroborated_fields = sum(
            len({item.source_url for item in field_items[field]}) > 1
            for field in supported_fields
        )
        score += min(
            self.MAX_CORROBORATION_BONUS,
            corroborated_fields * self.CORROBORATION_BONUS_PER_FIELD,
        )
        return round(min(score, 1.0), 2)

    @staticmethod
    def _items_for(evidence: EvidencePack, *fields: str) -> list:
        return [
            item for item in evidence.items
            if item.field in fields and item.value.strip()
        ]
