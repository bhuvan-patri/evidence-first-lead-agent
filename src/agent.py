from src.evidence_builder import EvidenceBuilder
from src.gemini_extractor import GeminiExtractor
from src.profile_builder import ProfileBuilder
from src.site_analyzer import SiteAnalyzer
from src.telemetry import UsageTracker


class LeadEnrichmentAgent:
    """
    Orchestrates the complete lead-enrichment workflow.

    Each domain is processed independently so that a failure on one
    website does not terminate the entire run.
    """

    def __init__(
        self,
        headless: bool = True,
        max_pages: int = 5,
        llm_extractor=None,
        usage_tracker: UsageTracker | None = None,
    ):
        self.analyzer = SiteAnalyzer(
            headless=headless,
            max_pages=max_pages,
        )

        self.evidence_builder = EvidenceBuilder()

        self.usage_tracker = usage_tracker or UsageTracker()

        self.llm_extractor = llm_extractor or GeminiExtractor(
            usage_tracker=self.usage_tracker
        )

        self.profile_builder = ProfileBuilder()

    def enrich_domain(self, domain: str) -> dict:
        """
        Process a single company domain.

        Any failure is captured in the domain result instead of
        terminating the complete run.
        """
        try:
            analysis = self.analyzer.analyze(domain)

            if not analysis["success"]:
                return {
                    "domain": analysis["domain"],
                    "success": False,
                    "error": analysis["error"],
                    "profile": None,
                }

            evidence = self.evidence_builder.build(analysis)

            if not evidence.items:
                return {
                    "domain": analysis["domain"],
                    "success": False,
                    "error": "No usable evidence was collected.",
                    "profile": None,
                }

            draft = self.llm_extractor.extract(evidence)

            profile = self.profile_builder.build(
                draft=draft,
                evidence=evidence,
            )

            return {
                "domain": analysis["domain"],
                "success": True,
                "error": None,
                "pages_discovered": analysis["pages_discovered"],
                "pages_selected": analysis["pages_selected"],
                "evidence_items": len(evidence.items),
                "profile": profile,
            }

        except Exception as exc:
            return {
                "domain": domain,
                "success": False,
                "error": f"{type(exc).__name__}: {exc}",
                "profile": None,
            }

    def enrich_domains(self, domains: list[str]) -> list[dict]:
        """
        Process multiple domains independently.
        """
        results = []

        for domain in domains:
            results.append(
                self.enrich_domain(domain)
            )

        return results

    def telemetry_summary(self) -> dict:
        """
        Return usage statistics for the current agent run.
        """
        return self.usage_tracker.summary()