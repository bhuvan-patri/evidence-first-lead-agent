from src.search import SearchProvider, SearchResult
from src.fallback_controller import FallbackController


class FakeSearchProvider(SearchProvider):
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return [
            SearchResult(
                title=query,
                url="https://example.com/result",
                snippet="Example evidence",
            )
        ]


def test_searches_only_missing_goals():
    controller = FallbackController(FakeSearchProvider())

    pages = [
        {
            "success": True,
            "goal": "company_overview",
        },
        {
            "success": True,
            "goal": "contact_information",
        },
    ]

    results = controller.find_missing_evidence(
        "postman.com",
        pages,
    )

    assert set(results.keys()) == {
        "leadership",
        "target_audience",
    }

    assert len(results["leadership"]) == 1
    assert len(results["target_audience"]) == 1