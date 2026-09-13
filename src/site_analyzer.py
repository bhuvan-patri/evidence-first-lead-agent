from src.evidence_classifier import EvidenceClassifier
from src.evidence_collector import EvidenceCollector
from src.link_discovery import LinkDiscovery
from src.planner import InformationPlanner


class SiteAnalyzer:
    """
    Adaptive website analyzer.

    The analyzer does not blindly crawl a fixed list of pages.
    It continuously checks which information goals still need evidence
    and chooses the next most relevant page accordingly.
    """

    REQUIRED_GOALS = {
        "company_overview",
        "target_audience",
        "contact_information",
        "leadership",
    }

    USABLE_STRENGTHS = {
        "strong",
        "medium",
    }

    def __init__(
        self,
        headless: bool = True,
        max_pages: int = 5,
    ):
        self.discovery = LinkDiscovery(
            headless=headless
        )
        self.collector = EvidenceCollector(
            headless=headless
        )
        self.planner = InformationPlanner()
        self.classifier = EvidenceClassifier()
        self.max_pages = max_pages

    def _classify_page(self, page: dict) -> dict:
        """
        Classify the evidence found on a page.

        Only successful pages are classified.
        """

        if not page.get("success"):
            return {
                **page,
                "goals": [],
                "signals": [],
            }

        signals = self.classifier.classify(
            page.get("content", "")
        )

        return {
            **page,
            "goals": [
                signal.goal
                for signal in signals
            ],
            "signals": [
                {
                    "goal": signal.goal,
                    "strength": signal.strength,
                    "reason": signal.reason,
                }
                for signal in signals
            ],
        }

    def _get_completed_goals(
        self,
        pages: list[dict],
    ) -> set[str]:
        """
        Return goals supported by at least medium-strength evidence.

        Weak signals are intentionally ignored so that navigation noise
        does not make the agent believe a goal has been completed.
        """

        completed = set()

        for page in pages:
            if not page.get("success"):
                continue

            for signal in page.get("signals", []):
                strength = signal.get(
                    "strength",
                    "",
                )

                if strength in self.USABLE_STRENGTHS:
                    completed.add(
                        signal["goal"]
                    )

        return completed

    def _get_missing_goals(
        self,
        pages: list[dict],
    ) -> set[str]:
        completed = self._get_completed_goals(
            pages
        )

        return (
            self.REQUIRED_GOALS
            - completed
        )

    def _rank_for_missing_goals(
        self,
        links: list[dict],
        missing_goals: set[str],
        visited_urls: set[str],
    ) -> list[dict]:
        """
        Re-rank available links according to the goals that are
        currently missing.

        This is the core of the adaptive browsing behavior.
        """

        candidates = []

        for link in links:
            url = link.get("url")

            if not url:
                continue

            if url in visited_urls:
                continue

            goal = link.get("goal")

            if goal not in missing_goals:
                continue

            goal_priority = link.get(
                "goal_priority",
                0,
            )

            goal_score = link.get(
                "goal_score",
                0,
            )

            link_score = link.get(
                "score",
                0,
            )

            candidates.append(
                {
                    **link,
                    "_adaptive_score": (
                        goal_priority * 100
                        + goal_score * 10
                        + link_score
                    ),
                }
            )

        candidates.sort(
            key=lambda item: item[
                "_adaptive_score"
            ],
            reverse=True,
        )

        return candidates

    def _select_next_page(
        self,
        links: list[dict],
        missing_goals: set[str],
        visited_urls: set[str],
    ) -> dict | None:
        candidates = self._rank_for_missing_goals(
            links=links,
            missing_goals=missing_goals,
            visited_urls=visited_urls,
        )

        if not candidates:
            return None

        return candidates[0]

    def analyze(self, domain: str) -> dict:
        """
        Analyze a company website using adaptive evidence collection.
        """

        if not domain.startswith(
            ("http://", "https://")
        ):
            domain = f"https://{domain}"

        homepage = self.collector.collect(
            domain
        )

        if not homepage["success"]:
            return {
                "domain": domain,
                "success": False,
                "pages": [],
                "error": homepage["error"],
            }

        homepage = self._classify_page(
            homepage
        )

        pages = [homepage]

        visited_urls = {
            homepage["url"]
        }

        # Link discovery is isolated from page collection.
        # A discovery failure should not erase the homepage evidence.
        try:
            links = self.discovery.discover(
                domain
            )
        except Exception:
            links = []

        ranked_links = self.planner.rank_links(
            links
        )

        pages_selected = 0

        while (
            pages_selected < self.max_pages
        ):
            missing_goals = self._get_missing_goals(
                pages
            )

            # Stop early when all required evidence
            # goals have usable evidence.
            if not missing_goals:
                break

            next_page = self._select_next_page(
                links=ranked_links,
                missing_goals=missing_goals,
                visited_urls=visited_urls,
            )

            if next_page is None:
                break

            url = next_page["url"]

            # Mark as visited before collection so even a
            # failed page cannot be selected repeatedly.
            visited_urls.add(url)

            try:
                evidence = self.collector.collect(
                    url
                )
            except Exception as exc:
                evidence = {
                    "url": url,
                    "success": False,
                    "title": "",
                    "content": "",
                    "sections": [],
                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }

            evidence = self._classify_page(
                evidence
            )

            evidence["goal"] = next_page.get(
                "goal"
            )
            evidence["goal_priority"] = (
                next_page.get(
                    "goal_priority",
                    0,
                )
            )
            evidence["goal_score"] = (
                next_page.get(
                    "goal_score",
                    0,
                )
            )

            pages.append(evidence)
            pages_selected += 1

        completed_goals = (
            self._get_completed_goals(pages)
        )

        missing_goals = (
            self.REQUIRED_GOALS
            - completed_goals
        )

        return {
            "domain": domain,
            "success": True,
            "pages": pages,
            "pages_discovered": len(
                ranked_links
            ),
            "pages_selected": pages_selected,
            "completed_goals": sorted(
                completed_goals
            ),
            "missing_goals": sorted(
                missing_goals
            ),
        }