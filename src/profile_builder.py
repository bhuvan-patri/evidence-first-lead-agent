from src.confidence import ConfidenceEngine
from src.evidence_pack import EvidencePack
from src.models import Evidence, LeadProfile, LeadProfileDraft


class ProfileBuilder:
    def __init__(self):
        self.confidence_engine = ConfidenceEngine()

    def build(
        self,
        draft: LeadProfileDraft,
        evidence: EvidencePack,
    ) -> LeadProfile:
        confidence = self.confidence_engine.calculate(
            profile=draft,
            evidence=evidence,
        )

        evidence_items = [
            Evidence(
                field=item.field,
                value=item.value,
                source_url=item.source_url,
                source_type=item.source_type,
            )
            for item in evidence.items
        ]

        return LeadProfile(
            **draft.model_dump(exclude={"evidence"}),
            evidence=evidence_items,
            confidence=confidence,
        )