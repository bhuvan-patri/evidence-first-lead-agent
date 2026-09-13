from src.search import SearchResult


def search_result_to_evidence(
    result: SearchResult,
    goal: str,
) -> dict:
    return {
        "field": goal,
        "value": result.snippet,
        "source_url": result.url,
        "source_type": "external_search",
    }