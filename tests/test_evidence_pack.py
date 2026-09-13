from src.evidence_pack import EvidenceItem, EvidencePack


def test_evidence_pack_groups_and_formats_evidence():
    pack = EvidencePack(company_domain="postman.com")

    pack.add(
        EvidenceItem(
            field="company_overview",
            value="API platform for building and using APIs.",
            source_url="https://postman.com/about",
            source_type="company_website",
        )
    )

    pack.add(
        EvidenceItem(
            field="leadership",
            value="Example Person - CEO",
            source_url="https://example.com/leadership",
            source_type="external_search",
        )
    )

    overview = pack.for_goal("company_overview")

    assert len(overview) == 1
    assert overview[0].value.startswith("API platform")

    text = pack.to_text()

    assert "company_overview" in text
    assert "leadership" in text
    assert "https://postman.com/about" in text
    assert "external_search" in text