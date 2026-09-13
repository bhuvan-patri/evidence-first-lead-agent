from src.gemini_extractor import GeminiExtractor
from src.models import LeadProfileDraft


class FakeInteraction:
    output_text = LeadProfileDraft(
        company_domain="example.com",
        company_overview="Example Analytics provides cloud-based analytics software.",
        icp="Enterprise data teams and business analysts.",
        generic_emails=[],
        leadership=[],
        evidence=[],
    ).model_dump_json()


class FakeInteractions:
    def create(self, **kwargs):
        return FakeInteraction()


class FakeClient:
    def __init__(self):
        self.interactions = FakeInteractions()


def test_gemini_extractor_returns_structured_profile(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    extractor = GeminiExtractor()
    extractor.client = FakeClient()

    from src.evidence_pack import EvidencePack

    evidence = EvidencePack(company_domain="example.com")

    result = extractor.extract(evidence)

    assert isinstance(result, LeadProfileDraft)
    assert result.company_domain == "example.com"
    assert result.company_overview
    assert result.icp