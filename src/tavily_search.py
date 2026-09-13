import os

from tavily import TavilyClient

from src.search import SearchProvider, SearchResult


class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is not configured.")

        self.client = TavilyClient(api_key=self.api_key)

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        response = self.client.search(
            query=query,
            max_results=max_results,
        )

        results = []

        for item in response.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                )
            )

        return results