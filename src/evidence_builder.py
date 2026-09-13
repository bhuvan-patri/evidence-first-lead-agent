"""Build a compact, conservative evidence pack from cleaned rendered pages."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from src.evidence_classifier import EvidenceClassifier
from src.evidence_pack import EvidenceItem, EvidencePack


class EvidenceBuilder:
    MAX_SNIPPET_LENGTH = 900
    GENERIC_EMAIL = re.compile(r"\b(?:info|hello|sales|support|contact|help|press|media|partnerships?|legal|security|privacy)@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
    EXCLUDED_CONTEXT = re.compile(r"\b(pricing|plans?|subscription|free trial|customer stor(?:y|ies)|case stud(?:y|ies)|testimonial|review|what customers say)\b", re.I)
    LEADERSHIP_HEADING = re.compile(r"\b(leadership|executives?|founders?|management|our team|meet the team)\b", re.I)
    LEADERSHIP_ROLE = re.compile(r"\b(ceo|cto|coo|cfo|cmo|cpo|cro|cio|chief [a-z ]+ officer|co-?founder|president|vice president|vp of)\b", re.I)

    def __init__(self):
        self.classifier = EvidenceClassifier()

    def build(self, analysis: dict) -> EvidencePack:
        pack = EvidencePack(company_domain=analysis["domain"])
        seen: set[tuple[str, str]] = set()
        for page in analysis.get("pages", []):
            if not page.get("success") or not page.get("content", "").strip():
                continue
            source_type = page.get("source_type", "company_website")
            for signal in self.classifier.classify(page["content"], page.get("url", "")):
                if signal.strength == "weak":
                    continue
                value = self._snippet(page, signal.goal)
                key = (signal.goal, value.casefold())
                if value and key not in seen:
                    pack.add(EvidenceItem(field=signal.goal, value=value, source_url=page["url"],
                                          source_type=source_type, strength=signal.strength))
                    seen.add(key)
        return pack

    def _snippet(self, page: dict, goal: str) -> str:
        lines = [line.strip() for line in page.get("content", "").splitlines() if line.strip()]
        if goal == "contact_information":
            return self._limit("\n".join(line for line in lines if self.GENERIC_EMAIL.search(line)))
        sections = page.get("sections", [])
        if goal == "leadership":
            sections = [section for section in sections if self.LEADERSHIP_HEADING.search(section.get("heading", "")) and not self.EXCLUDED_CONTEXT.search(section.get("heading", ""))]
            candidates = [
                f"{section.get('heading', '')}\n{section.get('content', '')}"
                for section in sections
                if self.LEADERSHIP_ROLE.search(section.get("content", ""))
                and self.classifier.has_named_leader(
                    f"{section.get('heading', '')}\n{section.get('content', '')}"
                )
            ]
            # LinkedIn profile anchors are useful only alongside genuine
            # first-party leadership context. They are kept verbatim so the
            # structured extractor can return a URL only when it was actually
            # present in the rendered page.
            if not candidates:
                return ""
            linkedin_lines = []
            for link in page.get("links", []):
                if not isinstance(link, dict):
                    continue
                href = str(link.get("href", "")).strip()
                parsed = urlparse(href)
                if not parsed.netloc.lower().endswith("linkedin.com") or not parsed.path.lower().startswith("/in/"):
                    continue
                label = " ".join(str(link.get("text", "")).split()) or "Team member"
                linkedin_lines.append(f"LinkedIn profile: {label} — {href}")
            candidates.extend(linkedin_lines)
            return self._limit("\n".join(candidates))
        matcher = self.classifier.COMPANY_DESCRIPTION_PATTERN if goal == "company_overview" else self.classifier.AUDIENCE_PATTERN
        if goal == "company_overview":
            sections = sorted(
                sections,
                key=lambda section: not self.classifier.OVERVIEW_SECTION_PATTERN.search(section.get("heading", "")),
            )
        candidates: list[str] = []
        for section in sections:
            context = f"{section.get('heading', '')}\n{section.get('content', '')}"
            if self.EXCLUDED_CONTEXT.search(context):
                continue
            matches = [
                line.strip() for line in context.splitlines()
                if matcher.search(line)
                and (goal != "company_overview" or line in self.classifier.overview_lines(context, page.get("url", "")))
                and (goal != "target_audience" or self.classifier.is_explicit_audience_line(line))
            ]
            if matches:
                candidates.extend(matches[:3])
        if not candidates:
            candidates = [
                line for line in lines
                if matcher.search(line)
                and not self.EXCLUDED_CONTEXT.search(line)
                and (goal != "company_overview" or line in self.classifier.overview_lines(page["content"], page.get("url", "")))
                and (goal != "target_audience" or self.classifier.is_explicit_audience_line(line))
            ]
        return self._limit("\n".join(dict.fromkeys(candidates[:5])))

    def completed_goals(self, pages: list[dict]) -> set[str]:
        """Goals are complete only when non-empty evidence reaches the pack."""
        pack = self.build({"domain": "", "pages": pages})
        return {item.field for item in pack.items if item.value.strip()}

    def _limit(self, text: str) -> str:
        text = text.strip()
        return text if len(text) <= self.MAX_SNIPPET_LENGTH else f"{text[:self.MAX_SNIPPET_LENGTH].rstrip()}..."
