from src.evidence_builder import EvidenceBuilder
from src.site_analyzer import SiteAnalyzer


def test_evidence_builder_with_real_site():
    analyzer = SiteAnalyzer(headless=True, max_pages=3)

    analysis = analyzer.analyze("postman.com")

    assert analysis["success"] is True
    assert len(analysis["pages"]) > 0

    builder = EvidenceBuilder()
    evidence = builder.build(analysis)

    assert evidence.company_domain == "https://postman.com"
    assert len(evidence.items) > 0

    for item in evidence.items:
        assert item.value
        assert item.source_url
        assert item.source_type == "company_website"

    print("\nEvidence items collected:")
    for item in evidence.items:
        print(f"- [{item.field}] {item.source_url}")