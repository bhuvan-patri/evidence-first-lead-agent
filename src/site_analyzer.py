"""Adaptive, page-budgeted first-party evidence collection."""

from __future__ import annotations

from src.evidence_classifier import EvidenceClassifier
from src.evidence_collector import EvidenceCollector
from src.evidence_builder import EvidenceBuilder
from src.link_discovery import LinkDiscovery
from src.planner import InformationPlanner


class SiteAnalyzer:
    REQUIRED_GOALS = {"company_overview", "target_audience", "contact_information", "leadership"}
    USABLE_STRENGTHS = {"strong", "medium"}

    def __init__(self, headless: bool = True, max_pages: int = 5):
        self.discovery = LinkDiscovery(headless=headless)
        self.collector = EvidenceCollector(headless=headless)
        self.planner = InformationPlanner()
        self.classifier = EvidenceClassifier()
        self.evidence_builder = EvidenceBuilder()
        self.max_pages = max(1, max_pages)

    def _classify_page(self, page: dict) -> dict:
        if not page.get("success"):
            return {**page, "goals": [], "signals": []}
        signals = self.classifier.classify(page.get("content", ""), page.get("url", ""))
        return {
            **page,
            "goals": [signal.goal for signal in signals if signal.strength in self.USABLE_STRENGTHS],
            "signals": [{"goal": signal.goal, "strength": signal.strength, "reason": signal.reason} for signal in signals],
        }

    def completed_goals(self, pages: list[dict]) -> set[str]:
        return self.evidence_builder.completed_goals(pages)

    def _next_page(
        self,
        links: dict[str, dict],
        missing: set[str],
        visited: set[str],
        attempts_by_goal: dict[str, int],
    ) -> dict | None:
        candidates = []
        for url, link in links.items():
            if url in visited:
                continue
            scored = self.planner.best_goal_for(link, missing)
            if scored:
                # A high-value unresolved goal gets first choice, but a page
                # that failed to satisfy it must not consume the full budget.
                scored["_adaptive_score"] = (
                    scored["goal_priority"] * 100
                    + scored["goal_score"] * 10
                    + scored.get("score", 0)
                    - attempts_by_goal.get(scored["goal"], 0) * 300
                )
                candidates.append(scored)
        return max(candidates, key=lambda candidate: candidate["_adaptive_score"]) if candidates else None

    def analyze(self, domain: str) -> dict:
        homepage_url = domain if domain.startswith(("http://", "https://")) else f"https://{domain}"
        homepage = self._classify_page(self.collector.collect(homepage_url))
        if not homepage.get("success"):
            return {"domain": homepage_url, "success": False, "pages": [], "error": homepage.get("error", "Homepage unavailable")}

        pages = [homepage]
        visited = {homepage["url"].rstrip("/")}
        links = {link["url"]: link for link in self.discovery.discover_from_page(homepage)}
        selected = 0
        attempts_by_goal: dict[str, int] = {}

        while len(pages) < self.max_pages:
            missing = self.REQUIRED_GOALS - self.completed_goals(pages)
            if not missing:
                break
            candidate = self._next_page(links, missing, visited, attempts_by_goal)
            if candidate is None:
                break
            visited.add(candidate["url"])
            attempts_by_goal[candidate["goal"]] = attempts_by_goal.get(candidate["goal"], 0) + 1
            page = self._classify_page(self.collector.collect(candidate["url"]))
            page.update({"goal": candidate["goal"], "goal_priority": candidate["goal_priority"], "goal_score": candidate["goal_score"]})
            pages.append(page)
            selected += 1
            if page.get("success"):
                for link in self.discovery.discover_from_page(page):
                    links.setdefault(link["url"], link)

        completed = self.completed_goals(pages)
        return {
            "domain": homepage_url, "success": True, "pages": pages,
            "pages_discovered": len(links), "pages_selected": selected,
            "completed_goals": sorted(completed), "missing_goals": sorted(self.REQUIRED_GOALS - completed),
        }
