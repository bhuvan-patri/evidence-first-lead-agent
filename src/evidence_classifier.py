import re
from dataclasses import dataclass
from urllib.parse import urlparse

from src.models import EMAIL_PATTERN, normalize_generic_email


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

    EMAIL_PATTERN = EMAIL_PATTERN

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

    # These paths are editorial customer/review content, rather than a first-
    # party description of the company itself. The path check is deliberately
    # narrow: a legitimate About page may still mention customers.
    CUSTOMER_STORY_PATH_PATTERN = re.compile(
        r"/(?:customers?|case-stud(?:y|ies)|customer-stor(?:y|ies)|testimonials?|reviews?)(?:/|$)",
        re.IGNORECASE,
    )
    CUSTOMER_STORY_LABEL_PATTERN = re.compile(
        r"\b(?:customer stor(?:y|ies)|case stud(?:y|ies)|testimonials?|reviews?|what our customers say)\b",
        re.IGNORECASE,
    )
    CUSTOMER_QUOTE_LANGUAGE_PATTERN = re.compile(
        r"\b(?:we(?:'ve| have)?\s+(?:never\s+)?(?:bought|used|chose|selected)|our customer|customer quote)\b",
        re.IGNORECASE,
    )
    NAMED_CUSTOMER_ATTRIBUTION_PATTERN = re.compile(
        r"\b[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3},\s*"
        r"(?:lead|senior|staff|principal|product|engineering|software|support|"
        r"customer success|operations|marketing|sales)\s+[A-Za-z ]{2,40},\s*"
        r"[A-Z][A-Za-z0-9&.' -]{1,60}\b",
    )
    CTA_OR_FORM_LINE_PATTERN = re.compile(
        r"^(?:how can we help you|contact (?:us|sales)|talk to (?:sales|an expert)|"
        r"speak to (?:sales|an expert)|book (?:a )?demo|request (?:a )?demo|"
        r"get started|submit|send(?: message)?|name|email|work email|company|"
        r"phone(?: number)?|message|comments?)\*?[?!.:]*$",
        re.IGNORECASE,
    )
    PERSON_NAME_PATTERN = re.compile(
        r"\b[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3}\b"
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
        r"quote from|"
        r"sales strategy|"
        r"demand generation|"
        r"demand qualification|"
        r"self-serve conversion|"
        r"self serve conversion|"
        r"sales-assisted motion|"
        r"sales assisted motion|"
        r"pricing strategy|"
        r"business model"
        r")\b",
        re.IGNORECASE,
    )

    def classify(
        self,
        text: str,
        source_url: str = "",
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

        overview = self._classify_overview(normalized, source_url)
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
        if any(normalize_generic_email(match.group()) for match in self.EMAIL_PATTERN.finditer(text)):
            return EvidenceSignal(
                goal="contact_information",
                strength="strong",
                reason=(
                    "A public generic/business email address was detected."
                ),
            )
        # A contact CTA without a generic inbox is not enough to complete the
        # assignment's contact goal; otherwise the planner may stop before it
        # reaches a footer or contact page containing sales@/support@.
        return None

    def _classify_leadership(
        self,
        text: str,
    ) -> EvidenceSignal | None:
        # Strongest case: the text explicitly associates
        # a leadership role with the company.
        if self.COMPANY_LEADERSHIP_CONTEXT_PATTERN.search(text) and self.has_named_leader(text):
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

            if self.has_named_leader(line):
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

        return None

    def _classify_overview(
        self,
        text: str,
        source_url: str = "",
    ) -> EvidenceSignal | None:
        if self.overview_lines(text, source_url):
            return EvidenceSignal(
                goal="company_overview",
                strength="strong",
                reason="Direct company-description language was detected.",
            )

        # A generic About link/heading is not evidence by itself. Treating it
        # as complete would stop the adaptive browser before it finds a direct
        # company description on the actual page.
        return None

    def overview_lines(self, text: str, source_url: str = "") -> list[str]:
        """Return direct company-description lines that are safe LLM evidence."""
        if self._is_customer_story_url(source_url):
            return []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        has_customer_story_quote = (
            bool(self.CUSTOMER_STORY_LABEL_PATTERN.search(text))
            and bool(self.NAMED_CUSTOMER_ATTRIBUTION_PATTERN.search(text))
        )
        return [
            line for line in lines
            if self.COMPANY_DESCRIPTION_PATTERN.search(line)
            and not self.OVERVIEW_EXCLUSION_PATTERN.search(line)
            and not self._is_cta_or_form_line(line)
            and not self._is_customer_quote_line(line, has_customer_story_quote)
        ]

    def has_named_leader(self, text: str) -> bool:
        """Require a name and an executive/founder role, not a nav heading."""
        return bool(
            self.LEADERSHIP_ROLE_PATTERN.search(text)
            and self.PERSON_NAME_PATTERN.search(text)
        )

    def _is_customer_story_url(self, source_url: str) -> bool:
        return bool(self.CUSTOMER_STORY_PATH_PATTERN.search(urlparse(source_url).path))

    def _is_customer_quote_line(self, line: str, has_customer_story_quote: bool) -> bool:
        if self.CUSTOMER_QUOTE_LANGUAGE_PATTERN.search(line):
            return True
        if self.NAMED_CUSTOMER_ATTRIBUTION_PATTERN.search(line) and line.lower().startswith("we "):
            return True
        return has_customer_story_quote and bool(self.NAMED_CUSTOMER_ATTRIBUTION_PATTERN.search(line))

    def _is_cta_or_form_line(self, line: str) -> bool:
        normalized = line.strip().rstrip("*").rstrip("?!.:").strip()
        return bool(self.CTA_OR_FORM_LINE_PATTERN.fullmatch(normalized))

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
            if self.is_explicit_audience_line(line):
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

    def is_explicit_audience_line(self, line: str) -> bool:
        """Reject GTM and sales-funnel wording even when it mentions a role."""
        return bool(
            self.AUDIENCE_PATTERN.search(line)
            and not self.AUDIENCE_EXCLUSION_PATTERN.search(line)
        )
