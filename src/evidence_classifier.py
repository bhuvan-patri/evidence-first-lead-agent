import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceSignal:
    goal: str
    strength: str
    reason: str


class EvidenceClassifier:
    """
    Classifies rendered webpage content into information goals.

    Strength levels:
        strong -> direct, specific evidence
        medium -> meaningful contextual evidence
        weak   -> weak/general signal

    The classifier is intentionally conservative. It is better to leave
    a goal unresolved than to incorrectly mark unrelated page content
    as useful evidence.
    """

    EMAIL_PATTERN = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    LEADERSHIP_ROLE_PATTERN = re.compile(
        r"\b("
        r"chief executive officer|"
        r"chief technology officer|"
        r"chief operating officer|"
        r"chief financial officer|"
        r"chief marketing officer|"
        r"chief product officer|"
        r"chief revenue officer|"
        r"chief information officer|"
        r"ceo|cto|coo|cfo|cmo|cpo|cro|cio|"
        r"founder|co-founder|"
        r"president|"
        r"vice president|"
        r"vp of|"
        r"executive"
        r")\b",
        re.IGNORECASE,
    )

    LEADERSHIP_SECTION_PATTERN = re.compile(
        r"\b("
        r"leadership team|"
        r"executive team|"
        r"our leadership|"
        r"our executives|"
        r"meet our team|"
        r"meet the team|"
        r"the founders|"
        r"our founders|"
        r"management team|"
        r"company leadership"
        r")\b",
        re.IGNORECASE,
    )

    COMPANY_LEADERSHIP_CONTEXT_PATTERN = re.compile(
        r"\b("
        r"our\s+"
        r"(?:chief|ceo|cto|coo|cfo|cmo|cpo|cro|cio|"
        r"founder|co-founder|president|vice president|vp)"
        r"|"
        r"company\s+"
        r"(?:founder|co-founder|ceo|cto|president)"
        r"|"
        r"company's\s+"
        r"(?:founder|co-founder|ceo|cto|president)"
        r"|"
        r"founder\s+and\s+"
        r"(?:ceo|cto|president)"
        r"|"
        r"co-founder\s+and\s+"
        r"(?:ceo|cto|president)"
        r"|"
        r"co-founder\s*&\s*"
        r"(?:ceo|cto|president)"
        r"|"
        r"(?:ceo|cto|president)"
        r"\s+of\s+(?:the\s+)?company"
        r"|"
        r"(?:ceo|cto|coo|cfo|cmo|cpo|cro|cio)"
        r"\s+of\s+(?:the\s+)?"
        r"(?:company|organization)"
        r")\b",
        re.IGNORECASE,
    )

    EXTERNAL_LEADERSHIP_ATTRIBUTION_PATTERN = re.compile(
        r"(?:"
        r"\b(?:"
        r"ceo|cto|coo|cfo|cmo|cpo|cro|cio|"
        r"chief executive officer|"
        r"chief technology officer|"
        r"chief operating officer|"
        r"chief financial officer|"
        r"chief marketing officer|"
        r"chief product officer|"
        r"chief revenue officer|"
        r"chief information officer|"
        r"founder|co-founder|president|vice president|vp"
        r"|vp of"
        r")\b"
        r"\s*(?:,|-|–|—|\||\()"
        r"\s*[A-Z][A-Za-z0-9&.'() -]{2,}"
        r")"
        r"|"
        r"\b[A-Z][A-Za-z.'-]+"
        r"(?:\s+[A-Z][A-Za-z.'-]+){0,3}"
        r"\s*,\s*"
        r"(?:CEO|CTO|COO|CFO|CMO|CPO|CRO|CIO|"
        r"Founder|Co-founder|VP|Vice President)"
        r"\b",
        re.IGNORECASE,
    )

    CONTACT_PATTERN = re.compile(
        r"\b("
        r"contact us|"
        r"contact our|"
        r"get in touch|"
        r"talk to sales|"
        r"contact sales|"
        r"sales team|"
        r"customer support|"
        r"support team|"
        r"reach us|"
        r"contact information|"
        r"contact details"
        r")\b",
        re.IGNORECASE,
    )

    # Phrases that directly describe what the company does.
    COMPANY_DESCRIPTION_PATTERN = re.compile(
        r"\b("
        r"we build|"
        r"we provide|"
        r"we develop|"
        r"we create|"
        r"we help|"
        r"we enable|"
        r"we make|"
        r"we offer|"
        r"we are a|"
        r"we're a|"
        r"our company|"
        r"our mission|"
        r"our vision|"
        r"our story|"
        r"who we are|"
        r"about us|"
        r"company overview|"
        r"founded in|"
        r"founded by|"
        r"headquartered in|"
        r"is a leading|"
        r"is an? [a-z]+ company|"
        r"platform for|"
        r"software for|"
        r"technology for"
        r")\b",
        re.IGNORECASE,
    )

    OVERVIEW_SECTION_PATTERN = re.compile(
        r"\b("
        r"about|"
        r"about us|"
        r"our story|"
        r"who we are|"
        r"company overview|"
        r"our mission|"
        r"our vision"
        r")\b",
        re.IGNORECASE,
    )

    AUDIENCE_PATTERN = re.compile(
        r"\b("
        r"built for|"
        r"designed for|"
        r"made for|"
        r"created for|"
        r"developed for|"
        r"intended for|"
        r"tailored for|"
        r"for developers|"
        r"for engineering teams|"
        r"for enterprise teams|"
        r"for businesses|"
        r"for startups|"
        r"for enterprises|"
        r"for organizations|"
        r"for builders|"
        r"for ai builders|"
        r"for data teams|"
        r"for product teams|"
        r"for security teams|"
        r"for marketing teams|"
        r"for sales teams|"
        r"our customers|"
        r"our users|"
        r"who uses|"
        r"customer segments|"
        r"target audience|"
        r"target customers|"
        r"ideal customers?|"
        r"ideal users?"
        r")\b",
        re.IGNORECASE,
    )

    # Signals that indicate the text is primarily about pricing,
    # transactions, or an individual customer rather than the company.
    OVERVIEW_EXCLUSION_PATTERN = re.compile(
        r"\b("
        r"pricing|"
        r"price|"
        r"plans?|"
        r"subscription|"
        r"per month|"
        r"per year|"
        r"free trial|"
        r"customer story|"
        r"customer stories|"
        r"case study|"
        r"case studies|"
        r"testimonial|"
        r"testimonials|"
        r"reviews?|"
        r"quote from|"
        r"what our customers say"
        r")\b",
        re.IGNORECASE,
    )

    AUDIENCE_EXCLUSION_PATTERN = re.compile(
        r"\b("
        r"customer story|"
        r"customer stories|"
        r"case study|"
        r"case studies|"
        r"testimonial|"
        r"testimonials|"
        r"review|"
        r"reviews|"
        r"quote from"
        r")\b",
        re.IGNORECASE,
    )

    def classify(
        self,
        text: str,
    ) -> list[EvidenceSignal]:
        if not text:
            return []

        normalized = self._normalize(text)

        signals = []

        contact = self._classify_contact(
            normalized
        )
        if contact:
            signals.append(contact)

        leadership = self._classify_leadership(
            normalized
        )
        if leadership:
            signals.append(leadership)

        overview = self._classify_overview(
            normalized
        )
        if overview:
            signals.append(overview)

        audience = self._classify_audience(
            normalized
        )
        if audience:
            signals.append(audience)

        return signals

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        lines = []

        for line in text.splitlines():
            cleaned = re.sub(
                r"\s+",
                " ",
                line,
            ).strip()

            if cleaned:
                lines.append(cleaned)

        return "\n".join(lines)

    def _classify_contact(
        self,
        text: str,
    ) -> EvidenceSignal | None:
        if self.EMAIL_PATTERN.search(text):
            return EvidenceSignal(
                goal="contact_information",
                strength="strong",
                reason=(
                    "A public email address was detected."
                ),
            )

        if self.CONTACT_PATTERN.search(text):
            return EvidenceSignal(
                goal="contact_information",
                strength="medium",
                reason=(
                    "Explicit contact or sales language "
                    "was detected."
                ),
            )

        return None

    def _classify_leadership(
        self,
        text: str,
    ) -> EvidenceSignal | None:
        # Strongest case: the text explicitly associates
        # a leadership role with the company.
        if self.COMPANY_LEADERSHIP_CONTEXT_PATTERN.search(
            text
        ):
            return EvidenceSignal(
                goal="leadership",
                strength="strong",
                reason=(
                    "A leadership role is explicitly "
                    "associated with the company."
                ),
            )

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        leadership_section_found = False
        valid_leadership_line_found = False

        for line in lines:
            if self.LEADERSHIP_SECTION_PATTERN.search(
                line
            ):
                leadership_section_found = True

            has_role = bool(
                self.LEADERSHIP_ROLE_PATTERN.search(
                    line
                )
            )

            if not has_role:
                continue

            if self.EXTERNAL_LEADERSHIP_ATTRIBUTION_PATTERN.search(
                line
            ):
                continue

            valid_leadership_line_found = True

        if (
            leadership_section_found
            and valid_leadership_line_found
        ):
            return EvidenceSignal(
                goal="leadership",
                strength="medium",
                reason=(
                    "A leadership section contains "
                    "executive-role information without "
                    "clear external attribution."
                ),
            )

        if leadership_section_found:
            return EvidenceSignal(
                goal="leadership",
                strength="medium",
                reason=(
                    "A dedicated leadership, founders, "
                    "or executive section was detected."
                ),
            )

        return None

    def _classify_overview(
        self,
        text: str,
    ) -> EvidenceSignal | None:
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        description_lines = [
            line
            for line in lines
            if self.COMPANY_DESCRIPTION_PATTERN.search(
                line
            )
        ]

        if description_lines:
            useful_lines = [
                line
                for line in description_lines
                if not self.OVERVIEW_EXCLUSION_PATTERN.search(
                    line
                )
            ]

            if useful_lines:
                return EvidenceSignal(
                    goal="company_overview",
                    strength="strong",
                    reason=(
                        "Direct company-description "
                        "language was detected."
                    ),
                )

        # A dedicated About/Mission/Story section is useful,
        # but without an explicit company description we keep
        # it at medium strength.
        overview_section_found = bool(
            self.OVERVIEW_SECTION_PATTERN.search(
                text
            )
        )

        if overview_section_found:
            return EvidenceSignal(
                goal="company_overview",
                strength="medium",
                reason=(
                    "A dedicated company overview, "
                    "about, mission, or story section "
                    "was detected."
                ),
            )

        return None

    def _classify_audience(
        self,
        text: str,
    ) -> EvidenceSignal | None:
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        audience_lines = []

        for line in lines:
            if not self.AUDIENCE_PATTERN.search(
                line
            ):
                continue

            if self.AUDIENCE_EXCLUSION_PATTERN.search(
                line
            ):
                continue

            audience_lines.append(line)

        if audience_lines:
            return EvidenceSignal(
                goal="target_audience",
                strength="strong",
                reason=(
                    "Explicit target-audience or "
                    "customer-segment language was detected."
                ),
            )

        return None