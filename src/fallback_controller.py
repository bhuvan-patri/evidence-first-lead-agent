from src.goal_tracker import GoalTracker
from src.search import SearchProvider
from src.search_fallback import SearchFallback


class FallbackController:
    def __init__(self, search_provider: SearchProvider):
        self.tracker = GoalTracker()
        self.fallback = SearchFallback(search_provider)

    def find_missing_evidence(
        self,
        company_domain: str,
        collected_pages: list[dict],
    ) -> dict[str, list]:
        missing_goals = self.tracker.find_missing(collected_pages)

        results = {}

        for goal in sorted(missing_goals):
            results[goal] = self.fallback.find_evidence(
                company_domain=company_domain,
                goal=goal,
                max_results=5,
            )

        return results