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

    assert score == 0.54


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

    assert score == 0.40


def test_medium_leadership_without_linkedin_cannot_produce_perfect_confidence():
    profile = LeadProfileDraft(
        company_domain="example.com",
        company_overview="Example provides API software.",
        icp="Developers.",
        generic_emails=["info@example.com"],
        leadership=[{"name": "Jane Doe", "role": "CEO"}],
        evidence=[],
    )
    evidence = EvidencePack(company_domain="example.com")
    evidence.items = [
        EvidenceItem("company_overview", "Example provides API software.", "https://example.com/about", "company_website", "strong"),
        EvidenceItem("target_audience", "Developers.", "https://example.com/solutions", "company_website", "strong"),
        EvidenceItem("contact_information", "info@example.com", "https://example.com/contact", "company_website", "strong"),
        EvidenceItem("leadership", "Jane Doe, CEO", "https://example.com/team", "company_website", "medium"),
    ]

    score = ConfidenceEngine().calculate(profile, evidence)

    assert 0.0 <= score < 1.0
    assert score == 0.87


def test_confidence_is_bounded_with_high_quality_complete_evidence():
    profile = LeadProfileDraft(
        company_domain="example.com",
        company_overview="Example provides API software.",
        icp="Developers.",
        generic_emails=["info@example.com"],
        leadership=[{
            "name": "Jane Doe", "role": "CEO",
            "linkedin_url": "https://www.linkedin.com/in/jane-doe/",
        }],
        evidence=[],
    )
    evidence = EvidencePack(company_domain="example.com")
    for field, value in (
        ("company_overview", "Example provides API software."),
        ("target_audience", "Developers."),
        ("contact_information", "info@example.com"),
        ("leadership", "Jane Doe, CEO"),
    ):
        evidence.add(EvidenceItem(field, value, f"https://example.com/{field}", "company_website", "strong"))

    score = ConfidenceEngine().calculate(profile, evidence)

    assert 0.0 <= score <= 1.0
    assert score == 0.95
