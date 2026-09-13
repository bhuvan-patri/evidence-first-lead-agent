from src.evidence import search_result_to_evidence
from src.search import SearchResult


def test_search_result_becomes_evidence():
    result = SearchResult(
        title="Postman Leadership",
        url="https://example.com/leadership",
        snippet="Leadership information.",
    )

    evidence = search_result_to_evidence(
        result,
        "leadership",
    )

    assert evidence["field"] == "leadership"
    assert evidence["value"] == "Leadership information."
    assert evidence["source_url"] == "https://example.com/leadership"
    assert evidence["source_type"] == "external_search"