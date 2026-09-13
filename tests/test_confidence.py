from src.confidence import ConfidenceEngine
from src.evidence_pack import EvidenceItem, EvidencePack
from src.models import LeadProfileDraft


def test_confidence_increases_with_supported_fields():
    engine = ConfidenceEngine()

    profile = LeadProfileDraft(
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

    score = engine.calculate(
        profile=profile,
        evidence=evidence,
    )

    assert score == 0.80


def test_confidence_is_zero_without_information():
    engine = ConfidenceEngine()

    profile = LeadProfileDraft(
        company_domain="example.com",
        company_overview="",
        icp="",
        generic_emails=[],
        leadership=[],
        evidence=[],
    )

    evidence = EvidencePack(company_domain="example.com")

    score = engine.calculate(
        profile=profile,
        evidence=evidence,
    )

    assert score == 0.0


def test_unsupported_leadership_does_not_increase_confidence():
    engine = ConfidenceEngine()

    profile = LeadProfileDraft(
        company_domain="example.com",
        company_overview="Example Analytics provides analytics software.",
        icp="Enterprise data teams.",
        generic_emails=[],
        leadership=[
            {
                "name": "John Doe",
                "role": "CEO",
            }
        ],
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

    score = engine.calculate(
        profile=profile,
        evidence=evidence,
    )

    assert score == 0.60