import re

from src.confidence import ConfidenceEngine
from src.evidence_pack import EvidencePack
from src.models import EMAIL_PATTERN, Evidence, LeadProfile, LeadProfileDraft, Telemetry, normalize_generic_email


class ProfileBuilder:
    VALID_EVIDENCE_STRENGTHS = {"strong", "medium"}
    STRENGTH_ORDER = {"strong": 2, "medium": 1}

    def __init__(self):
        self.confidence_engine = ConfidenceEngine()

    def build(
        self,
        draft: LeadProfileDraft,
        evidence: EvidencePack,
        telemetry: dict | None = None,
    ) -> LeadProfile:
        draft = self._reconcile(draft, evidence)
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
                strength=item.strength,
            )
            for item in evidence.items
        ]

        return LeadProfile(
            **draft.model_dump(exclude={"evidence"}),
            evidence=evidence_items,
            confidence=confidence,
            telemetry=Telemetry.model_validate(telemetry or {}),
        )

    def _reconcile(self, draft: LeadProfileDraft, evidence: EvidencePack) -> LeadProfileDraft:
        """Make the post-LLM profile no broader than its validated evidence."""
        overview_items = self._valid_items(evidence, "company_overview")
        audience_items = self._valid_items(evidence, "target_audience", "icp")
        contact_items = self._valid_items(evidence, "contact_information")
        leadership_items = self._valid_items(evidence, "leadership")

        return draft.model_copy(update={
            "company_overview": self._reconcile_text(draft.company_overview, overview_items),
            "icp": self._reconcile_text(draft.icp, audience_items),
            "generic_emails": self._reconcile_emails(draft.generic_emails, contact_items),
            "leadership": self._reconcile_leadership(draft.leadership, leadership_items),
        })

    def _valid_items(self, evidence: EvidencePack, *fields: str) -> list:
        return [
            item for item in evidence.items
            if item.field in fields
            and item.value.strip()
            and item.strength in self.VALID_EVIDENCE_STRENGTHS
        ]

    def _reconcile_text(self, value: str, items: list) -> str:
        if not items:
            return ""
        source_value = self._strongest_value(items)
        if not value.strip() or not self._is_supported_text(value, items):
            return source_value
        return value

    def _reconcile_emails(self, emails: list[str], items: list) -> list[str]:
        if not items:
            return []
        evidence_emails: list[str] = []
        for item in items:
            for match in EMAIL_PATTERN.finditer(item.value):
                email = normalize_generic_email(match.group())
                if email and email not in evidence_emails:
                    evidence_emails.append(email)
        if not evidence_emails:
            return []
        # Exact email membership is deterministic; addresses are never inferred.
        supported = [email for email in emails if email in evidence_emails]
        return supported or evidence_emails

    def _reconcile_leadership(self, leadership: list, items: list) -> list:
        if not items:
            return []
        source_text = "\n".join(item.value.casefold() for item in items)
        supported = []
        for person in leadership:
            if person.name.casefold() not in source_text or person.role.casefold() not in source_text:
                continue
            if person.linkedin_url and person.linkedin_url.casefold() not in source_text:
                continue
            supported.append(person)
        # Names/roles are not parsed from prose: an empty LLM leadership list
        # remains empty rather than manufacturing a structured person record.
        return supported

    def _strongest_value(self, items: list) -> str:
        return max(
            items,
            key=lambda item: self.STRENGTH_ORDER.get(item.strength, 0),
        ).value

    @staticmethod
    def _is_supported_text(value: str, items: list) -> bool:
        normalized = re.sub(r"\s+", " ", value).strip().casefold()
        return bool(normalized) and any(
            normalized in re.sub(r"\s+", " ", item.value).strip().casefold()
            for item in items
        )
