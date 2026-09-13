from src.models import LeadProfile


def test_lead_profile_schema_accepts_empty_optional_data():
    profile = LeadProfile(
        company_domain="example.com",
        company_overview="Example company.",
        icp="Businesses",
        generic_emails=[],
        leadership=[],
        confidence=0.0,
    )

    assert profile.company_domain == "example.com"
    assert profile.generic_emails == []
    assert profile.leadership == []
    assert profile.confidence == 0.0