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
    assert result.confidence == 0.54
    assert result.company_domain == "example.com"
    assert result.company_overview
    assert result.icp


def test_reconciliation_clears_llm_overview_without_valid_evidence():
    draft = LeadProfileDraft(
        company_domain="example.com",
        company_overview="An unsupported LLM company description.",
    )
    evidence = EvidencePack(company_domain="example.com")
    evidence.add(EvidenceItem(
        field="target_audience", value="Built for developers.",
        source_url="https://example.com/", source_type="company_website", strength="strong",
    ))

    result = ProfileBuilder().build(draft=draft, evidence=evidence)

    assert result.company_overview == ""


def test_reconciliation_uses_valid_overview_when_llm_returns_empty():
    draft = LeadProfileDraft(company_domain="example.com", company_overview="")
    evidence = EvidencePack(company_domain="example.com")
    evidence.add(EvidenceItem(
        field="company_overview", value="One platform for all your voice agents.",
        source_url="https://example.com/", source_type="company_website", strength="strong",
    ))

    result = ProfileBuilder().build(draft=draft, evidence=evidence)

    assert result.company_overview == "One platform for all your voice agents."


def test_reconciliation_keeps_overview_empty_without_valid_evidence():
    draft = LeadProfileDraft(company_domain="example.com", company_overview="")
    evidence = EvidencePack(company_domain="example.com")
    evidence.add(EvidenceItem(
        field="company_overview", value="Weak unvalidated copy.",
        source_url="https://example.com/", source_type="company_website", strength="weak",
    ))

    result = ProfileBuilder().build(draft=draft, evidence=evidence)

    assert result.company_overview == ""


def test_reconciliation_replaces_unsupported_llm_overview_with_valid_evidence():
    draft = LeadProfileDraft(
        company_domain="example.com",
        company_overview="A hallucinated description unrelated to the source.",
    )
    evidence = EvidencePack(company_domain="example.com")
    evidence.add(EvidenceItem(
        field="company_overview", value="Example provides secure API infrastructure.",
        source_url="https://example.com/about", source_type="company_website", strength="strong",
    ))

    result = ProfileBuilder().build(draft=draft, evidence=evidence)

    assert result.company_overview == "Example provides secure API infrastructure."
