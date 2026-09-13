"""Top-level orchestration: browser evidence, optional validated search, Gemini."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from src.evidence_builder import EvidenceBuilder
from src.fallback_controller import FallbackController
from src.gemini_extractor import GeminiExtractor
from src.profile_builder import ProfileBuilder
from src.site_analyzer import SiteAnalyzer
from src.tavily_search import TavilySearchProvider
from src.telemetry import UsageTracker


class LeadEnrichmentAgent:
    """Processes domains independently; no heuristic profile is substituted for Gemini."""

    def __init__(self, headless: bool = True, max_pages: int = 5, llm_extractor=None,
                 usage_tracker: UsageTracker | None = None, search_provider=None):
        self.analyzer = SiteAnalyzer(headless=headless, max_pages=max_pages)
        self.evidence_builder = EvidenceBuilder()
        self.usage_tracker = usage_tracker or UsageTracker()
        self.llm_extractor = llm_extractor or GeminiExtractor(usage_tracker=self.usage_tracker)
        self.profile_builder = ProfileBuilder()
        self.search_provider = search_provider or self._configured_search_provider()

    @staticmethod
    def _configured_search_provider():
        if not os.getenv("TAVILY_API_KEY"):
            return None
        try:
            return TavilySearchProvider()
        except Exception:
            return None

    @staticmethod
    def _host(domain: str) -> str:
        return urlparse(domain if "://" in domain else f"https://{domain}").netloc

    def _enrich_missing_goals(self, analysis: dict) -> None:
        """Validate a small number of search results in the browser before use."""
        if not self.search_provider:
            return
        company_domain = self._host(analysis["domain"])
        controller = FallbackController(self.search_provider)
        try:
            results_by_goal = controller.find_missing_evidence(company_domain, analysis["pages"])
        except Exception:
            return
        if "leadership" in results_by_goal:
            try:
                results_by_goal["leadership"].extend(
                    controller.fallback.find_linkedin_profiles(company_domain)
                )
            except Exception:
                pass
        for goal, results in results_by_goal.items():
            for result in results[:2]:
                try:
                    page = self.analyzer.collector.collect(result.url)
                except Exception:
                    continue
                if not page.get("success") or not page.get("content"):
                    continue
                result_host = self._host(page["url"])
                if goal == "leadership" and result_host != company_domain and not result_host.endswith("linkedin.com"):
                    continue
                page = self.analyzer._classify_page(page)
                if goal not in page.get("goals", []):
                    continue
                page["goal"] = goal
                page["source_type"] = "company_website" if self._host(page["url"]) == company_domain else "external_validated"
                analysis["pages"].append(page)
        completed = self.analyzer.completed_goals(analysis["pages"])
        analysis["completed_goals"] = sorted(completed)
        analysis["missing_goals"] = sorted(self.analyzer.REQUIRED_GOALS - completed)

    def enrich_domain(self, domain: str) -> dict:
        """Return a structured success/failure result for exactly one domain."""
        start = len(self.usage_tracker.records)
        try:
            analysis = self.analyzer.analyze(domain)
            if not analysis["success"]:
                return {"domain": analysis["domain"], "success": False, "error": analysis["error"],
                        "profile": None, "telemetry": self.usage_tracker.summary(start=start)}
            self._enrich_missing_goals(analysis)
            evidence = self.evidence_builder.build(analysis)
            if not evidence.items:
                return {"domain": analysis["domain"], "success": False, "error": "No usable evidence was collected.",
                        "profile": None, "telemetry": self.usage_tracker.summary(start=start)}
            # Result metadata must reflect evidence actually sent to Gemini,
            # rather than an earlier page-level heuristic signal.
            completed = sorted({item.field for item in evidence.items if item.value.strip()})
            analysis["completed_goals"] = completed
            analysis["missing_goals"] = sorted(SiteAnalyzer.REQUIRED_GOALS - set(completed))
            draft = self.llm_extractor.extract(evidence)
            telemetry = self.usage_tracker.summary(start=start)
            profile = self.profile_builder.build(draft=draft, evidence=evidence, telemetry=telemetry)
            return {
                "domain": analysis["domain"], "success": True, "error": None,
                "pages_discovered": analysis.get("pages_discovered", 0), "pages_selected": analysis.get("pages_selected", 0),
                "completed_goals": analysis.get("completed_goals", []), "missing_goals": analysis.get("missing_goals", []),
                "evidence_items": len(evidence.items), "profile": profile, "telemetry": telemetry,
            }
        except Exception as exc:
            return {"domain": domain, "success": False, "error": f"{type(exc).__name__}: {exc}",
                    "profile": None, "telemetry": self.usage_tracker.summary(start=start)}

    def enrich_domains(self, domains: list[str]) -> list[dict]:
        return [self.enrich_domain(domain) for domain in domains]

    def telemetry_summary(self) -> dict:
        return self.usage_tracker.summary()
