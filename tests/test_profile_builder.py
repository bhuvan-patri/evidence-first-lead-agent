from src.evidence_pack import EvidenceItem, EvidencePack
from src.models import LeadProfile, LeadProfileDraft
from src.profile_builder import ProfileBuilder


def test_profile_builder_adds_calculated_confidence():
    draft = LeadProfileDraft(
        company_domain="example.com",
        company_overview="Example Analytics provides analytics software.",
        icp="Enterprise data teams.",
        generic_emails=["info@example.com"],
        leadership=[],
        evidence=[],
    )

    evidence = EvidencePack(company_domain="example.com")

    evidence.add(
        EvidenceItem(
            field="company_overview",
            value="Example Analytics provides analytics software.",
            source_url="https://example.com/about",
            source_type="company_website",
        )
    )

    evidence.add(
        EvidenceItem(
            field="target_audience",
            value="Enterprise data teams.",
            source_url="https://example.com/solutions",
            source_type="company_website",
        )
    )

    evidence.add(
        EvidenceItem(
            field="contact_information",
            value="info@example.com",
            source_url="https://example.com/contact",
            source_type="company_website",
        )
    )

    builder = ProfileBuilder()

    result = builder.build(
        draft=draft,
        evidence=evidence,
    )

    assert isinstance(result, LeadProfile)
    assert result.confidence == 0.80
    assert result.company_domain == "example.com"
    assert result.company_overview
    assert result.icp