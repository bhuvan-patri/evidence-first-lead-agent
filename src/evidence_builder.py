import re

from src.evidence_classifier import EvidenceClassifier
from src.evidence_pack import EvidenceItem, EvidencePack


class EvidenceBuilder:
    MIN_EVIDENCE_STRENGTH = {
        "strong": 2,
        "medium": 1,
        "weak": 0,
    }

    MAX_SNIPPET_LENGTH = 1200
    CONTEXT_LINES = 2

    EMAIL_PATTERN = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    EXTERNAL_ROLE_ATTRIBUTION_PATTERN = re.compile(
        r"\b("
        r"ceo|"
        r"cto|"
        r"coo|"
        r"cfo|"
        r"cmo|"
        r"cpo|"
        r"cro|"
        r"cio|"
        r"chief executive officer|"
        r"chief technology officer|"
        r"chief operating officer|"
        r"chief financial officer|"
        r"chief marketing officer|"
        r"chief product officer|"
        r"chief revenue officer|"
        r"chief information officer|"
        r"founder|"
        r"co-founder|"
        r"president|"
        r"vice president|"
        r"vp of"
        r")\b"
        r"\s*(?:,|-|–|—|\||\()\s*"
        r"[A-Z][A-Za-z0-9&.'() -]{2,}",
        re.IGNORECASE,
    )

    LEADERSHIP_CONTEXT_PATTERN = re.compile(
        r"\b("
        r"our leadership|"
        r"our executives|"
        r"our founders|"
        r"the founders|"
        r"leadership team|"
        r"executive team|"
        r"meet our team|"
        r"meet the team|"
        r"still lead the company|"
        r"lead the company|"
        r"leads the company|"
        r"company leadership"
        r")\b",
        re.IGNORECASE,
    )

    def __init__(self):
        self.classifier = EvidenceClassifier()

    def build(self, analysis: dict) -> EvidencePack:
        evidence_pack = EvidencePack(
            company_domain=analysis["domain"]
        )

        for page in analysis.get("pages", []):
            if not page.get("success"):
                continue

            content = page.get("content", "").strip()

            if not content:
                continue

            signals = self.classifier.classify(content)

            for signal in signals:
                if not self._is_usable_signal(signal.strength):
                    continue

                snippet = self._extract_evidence_snippet(
                    content=content,
                    sections=page.get("sections", []),
                    goal=signal.goal,
                )

                if not snippet:
                    continue

                evidence_pack.add(
                    EvidenceItem(
                        field=signal.goal,
                        value=snippet,
                        source_url=page["url"],
                        source_type="company_website",
                    )
                )

        return evidence_pack

    def _is_usable_signal(self, strength: str) -> bool:
        return (
            self.MIN_EVIDENCE_STRENGTH.get(strength, -1) >= 1
        )

    def _extract_evidence_snippet(
        self,
        content: str,
        sections: list[dict],
        goal: str,
    ) -> str:
        if goal == "leadership":
            snippet = self._extract_leadership_from_sections(
                sections
            )

            if snippet:
                return snippet

            return self._extract_leadership_snippet(
                content.splitlines()
            )

        if goal == "target_audience":
            snippet = self._extract_goal_from_sections(
                sections,
                self._audience_line,
            )

            if snippet:
                return snippet

        if goal == "company_overview":
            snippet = self._extract_goal_from_sections(
                sections,
                self._overview_line,
            )

            if snippet:
                return snippet

        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        if not lines:
            return ""

        if goal == "contact_information":
            return self._extract_contact_snippet(lines)

        if goal == "target_audience":
            return self._extract_matching_snippet(
                lines,
                self._audience_line,
            )

        if goal == "company_overview":
            return self._extract_matching_snippet(
                lines,
                self._overview_line,
            )

        return self._limit_length(
            "\n".join(lines)
        )

    def _extract_leadership_from_sections(
        self,
        sections: list[dict],
    ) -> str:
        """
        Prefer semantically labelled leadership sections.

        This preserves genuine company leadership information while
        avoiding executive names embedded in customer-story sections.
        """

        leadership_sections = []

        for section in sections:
            heading = section.get(
                "heading",
                "",
            ).strip()

            section_content = section.get(
                "content",
                "",
            ).strip()

            if not heading and not section_content:
                continue

            combined = (
                f"{heading}\n{section_content}"
            )

            if not self._leadership_section_heading(
                heading
            ):
                continue

            if not self._contains_company_leadership(
                combined
            ):
                continue

            leadership_sections.append(
                combined
            )

        if not leadership_sections:
            return ""

        cleaned_parts = []

        for section in leadership_sections:
            lines = [
                line.strip()
                for line in section.splitlines()
                if line.strip()
            ]

            valid_lines = [
                line
                for line in lines
                if not self._is_external_leadership_attribution(
                    line
                )
            ]

            if valid_lines:
                cleaned_parts.extend(valid_lines)

        if not cleaned_parts:
            return ""

        return self._limit_length(
            "\n".join(cleaned_parts)
        )

    def _leadership_section_heading(
        self,
        heading: str,
    ) -> bool:
        normalized = heading.lower().strip()

        leadership_terms = (
            "leadership",
            "executive team",
            "executives",
            "founders",
            "founder",
            "our team",
            "meet the team",
            "meet our team",
            "management team",
        )

        return any(
            term in normalized
            for term in leadership_terms
        )

    def _contains_company_leadership(
        self,
        text: str,
    ) -> bool:
        if self.LEADERSHIP_CONTEXT_PATTERN.search(
            text
        ):
            return True

        company_patterns = [
            r"\bpostman['’]s\s+(?:ceo|cto|co-founder|founder)\b",
            r"\bour\s+(?:ceo|cto|co-founder|founder)\b",
            r"\bthe\s+(?:company|organization)['’]?s\s+"
            r"(?:ceo|cto|co-founder|founder)\b",
            r"\b(?:ceo|cto|co-founder|founder)"
            r"\s+(?:of|at)\s+(?:the\s+)?company\b",
            r"\b(?:ceo|cto|co-founder|founder)"
            r"\s+(?:of|at)\s+[A-Z][A-Za-z0-9 .&'-]+\b",
        ]

        return any(
            re.search(
                pattern,
                text,
                re.IGNORECASE,
            )
            for pattern in company_patterns
        )

    def _extract_goal_from_sections(
        self,
        sections: list[dict],
        matcher,
    ) -> str:
        """
        Extract evidence from the most relevant semantic sections
        instead of using arbitrary neighbouring lines.
        """

        candidates = []

        for section in sections:
            heading = section.get(
                "heading",
                "",
            ).strip()

            content = section.get(
                "content",
                "",
            ).strip()

            if not content:
                continue

            lines = [
                line.strip()
                for line in content.splitlines()
                if line.strip()
            ]

            matching_lines = [
                line
                for line in lines
                if matcher(line)
            ]

            if not matching_lines:
                continue

            heading_score = self._section_relevance_score(
                heading
            )

            candidates.append(
                (
                    heading_score,
                    len(matching_lines),
                    heading,
                    lines,
                )
            )

        if not candidates:
            return ""

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
            ),
            reverse=True,
        )

        _, _, heading, lines = candidates[0]

        selected_lines = self._select_relevant_lines(
            lines,
            matcher,
        )

        if heading:
            selected_lines.insert(
                0,
                heading,
            )

        return self._limit_length(
            "\n".join(selected_lines)
        )

    def _section_relevance_score(
        self,
        heading: str,
    ) -> int:
        normalized = heading.lower()

        scores = {
            "about": 6,
            "overview": 6,
            "platform": 5,
            "product": 5,
            "solutions": 5,
            "customers": 2,
            "customer stories": 1,
            "testimonials": 1,
            "use cases": 4,
            "industries": 4,
            "developers": 5,
            "teams": 4,
            "enterprise": 4,
        }

        score = 0

        for keyword, weight in scores.items():
            if keyword in normalized:
                score += weight

        return score

    def _select_relevant_lines(
        self,
        lines: list[str],
        matcher,
    ) -> list[str]:
        matching_indexes = [
            index
            for index, line in enumerate(lines)
            if matcher(line)
        ]

        if not matching_indexes:
            return []

        selected_indexes = set()

        for index in matching_indexes[:4]:
            start = max(
                0,
                index - 1,
            )

            end = min(
                len(lines),
                index + 2,
            )

            selected_indexes.update(
                range(start, end)
            )

        return [
            lines[index]
            for index in sorted(selected_indexes)
        ]

    def _extract_contact_snippet(
        self,
        lines: list[str],
    ) -> str:
        email_lines = [
            line
            for line in lines
            if self.EMAIL_PATTERN.search(line)
        ]

        if email_lines:
            return self._limit_length(
                "\n".join(email_lines)
            )

        return ""

    def _extract_leadership_snippet(
        self,
        lines: list[str],
    ) -> str:
        candidate_indexes = []

        for index, line in enumerate(lines):
            if not self._leadership_line(line):
                continue

            if self._is_external_leadership_attribution(
                line
            ):
                continue

            if self._has_company_leadership_context(
                lines,
                index,
            ):
                candidate_indexes.append(index)

        if not candidate_indexes:
            return ""

        selected_indexes = set()

        for index in candidate_indexes[:3]:
            start = max(
                0,
                index - self.CONTEXT_LINES,
            )

            end = min(
                len(lines),
                index + self.CONTEXT_LINES + 1,
            )

            for context_index in range(
                start,
                end,
            ):
                line = lines[context_index]

                if self._is_external_leadership_attribution(
                    line
                ):
                    continue

                selected_indexes.add(
                    context_index
                )

        snippet_lines = [
            lines[index]
            for index in sorted(selected_indexes)
        ]

        return self._limit_length(
            "\n".join(snippet_lines)
        )

    def _has_company_leadership_context(
        self,
        lines: list[str],
        index: int,
    ) -> bool:
        start = max(
            0,
            index - self.CONTEXT_LINES,
        )

        end = min(
            len(lines),
            index + self.CONTEXT_LINES + 1,
        )

        context = " ".join(
            lines[start:end]
        )

        if self.LEADERSHIP_CONTEXT_PATTERN.search(
            context
        ):
            return True

        return self._contains_company_leadership(
            context
        )

    def _is_external_leadership_attribution(
        self,
        line: str,
    ) -> bool:
        return bool(
            self.EXTERNAL_ROLE_ATTRIBUTION_PATTERN.search(
                line
            )
        )

    def _extract_matching_snippet(
        self,
        lines: list[str],
        matcher,
    ) -> str:
        matching_indexes = [
            index
            for index, line in enumerate(lines)
            if matcher(line)
        ]

        if not matching_indexes:
            return ""

        selected_indexes = set()

        for index in matching_indexes[:3]:
            start = max(
                0,
                index - self.CONTEXT_LINES,
            )

            end = min(
                len(lines),
                index + self.CONTEXT_LINES + 1,
            )

            selected_indexes.update(
                range(start, end)
            )

        snippet_lines = [
            lines[index]
            for index in sorted(selected_indexes)
        ]

        return self._limit_length(
            "\n".join(snippet_lines)
        )

    @staticmethod
    def _leadership_line(line: str) -> bool:
        pattern = re.compile(
            r"\b("
            r"leadership|"
            r"executive|"
            r"founder|"
            r"co-founder|"
            r"chief executive officer|"
            r"chief technology officer|"
            r"chief operating officer|"
            r"chief financial officer|"
            r"chief marketing officer|"
            r"chief product officer|"
            r"chief revenue officer|"
            r"chief information officer|"
            r"ceo|"
            r"cto|"
            r"coo|"
            r"cfo|"
            r"cmo|"
            r"cpo|"
            r"cro|"
            r"cio|"
            r"president|"
            r"vice president|"
            r"vp of"
            r")\b",
            re.IGNORECASE,
        )

        return bool(
            pattern.search(line)
        )

    @staticmethod
    def _audience_line(line: str) -> bool:
        pattern = re.compile(
            r"\b("
            r"built for|"
            r"designed for|"
            r"for developers|"
            r"for engineering teams|"
            r"for enterprise teams|"
            r"for businesses|"
            r"for startups|"
            r"for enterprises|"
            r"for organizations|"
            r"for data teams|"
            r"for product teams|"
            r"for security teams|"
            r"our customers|"
            r"customer segments|"
            r"target audience|"
            r"who uses"
            r")\b",
            re.IGNORECASE,
        )

        return bool(
            pattern.search(line)
        )

    @staticmethod
    def _overview_line(line: str) -> bool:
        pattern = re.compile(
            r"\b("
            r"about us|"
            r"our story|"
            r"who we are|"
            r"company overview|"
            r"our mission|"
            r"our vision|"
            r"founded in|"
            r"we build|"
            r"we provide|"
            r"our platform|"
            r"our product"
            r")\b",
            re.IGNORECASE,
        )

        return bool(
            pattern.search(line)
        )

    def _limit_length(
        self,
        text: str,
    ) -> str:
        if len(text) <= self.MAX_SNIPPET_LENGTH:
            return text

        return (
            text[: self.MAX_SNIPPET_LENGTH]
            .rstrip()
            + "..."
        )