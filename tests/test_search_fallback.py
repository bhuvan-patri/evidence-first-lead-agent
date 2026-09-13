from src.search import SearchProvider, SearchResult
from src.search_fallback import SearchFallback


class FakeSearchProvider(SearchProvider):
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return [
            SearchResult(
                title=query,
                url="https://example.com",
                snippet="Fake result",
            )
        ]


def test_leadership_query():
    fallback = SearchFallback(FakeSearchProvider())

    results = fallback.find_evidence(
        "postman.com",
        "leadership",
    )

    assert len(results) == 1
    assert "site:postman.com" in results[0].title
    assert "leadership" in results[0].title