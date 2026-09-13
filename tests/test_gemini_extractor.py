from src.gemini_extractor import DEFAULT_GEMINI_MODEL, GeminiExtractor
from src.models import LeadProfileDraft
from src.telemetry import UsageTracker
import pytest


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


def test_gemini_client_forces_developer_api_key_authentication(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-developer-api-key")
    captured = {}

    class Client:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("src.gemini_extractor.genai.Client", Client)

    GeminiExtractor()

    assert captured == {
        "api_key": "test-developer-api-key",
        "vertexai": False,
    }


def test_gemini_uses_3_6_flash_when_model_is_unset(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    extractor = GeminiExtractor()

    assert DEFAULT_GEMINI_MODEL == "gemini-3.6-flash"
    assert extractor.model == "gemini-3.6-flash"
    assert extractor.client is None


def test_gemini_records_usage_metadata(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    class Usage:
        total_input_tokens = 11
        total_output_tokens = 7
        total_thought_tokens = 2
        total_tokens = 20

    class Interaction(FakeInteraction):
        usage = Usage()

    class Client:
        class interactions:
            @staticmethod
            def create(**kwargs):
                return Interaction()

    tracker = UsageTracker()
    extractor = GeminiExtractor(usage_tracker=tracker)
    extractor.client = Client()
    result = extractor.extract(__import__("src.evidence_pack", fromlist=["EvidencePack"]).EvidencePack(company_domain="example.com"))
    assert result.company_domain == "example.com"
    assert tracker.summary()["total_tokens"] == 20


def test_gemini_estimates_cost_from_configured_rates(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_INPUT_USD_PER_1M_TOKENS", "2")
    monkeypatch.setenv("GEMINI_OUTPUT_USD_PER_1M_TOKENS", "3")
    monkeypatch.setenv("GEMINI_THOUGHT_USD_PER_1M_TOKENS", "1")

    class Usage:
        total_input_tokens = 1_000_000
        total_output_tokens = 1_000_000
        total_thought_tokens = 1_000_000
        total_tokens = 3_000_000

    class Interaction(FakeInteraction):
        usage = Usage()

    class Client:
        class interactions:
            @staticmethod
            def create(**kwargs):
                return Interaction()

    tracker = UsageTracker()
    extractor = GeminiExtractor(usage_tracker=tracker)
    extractor.client = Client()
    extractor.extract(__import__("src.evidence_pack", fromlist=["EvidencePack"]).EvidencePack(company_domain="example.com"))

    assert tracker.summary()["estimated_cost_usd"] == 6.0


def test_quota_exhaustion_429_is_not_retried(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    class QuotaError(Exception):
        pass

    class Interactions:
        calls = 0

        @classmethod
        def create(cls, **kwargs):
            cls.calls += 1
            raise QuotaError("429 generate_content_free_tier_requests: current quota exhausted")

    class Client:
        interactions = Interactions()

    extractor = GeminiExtractor(max_retries=2, retry_delay_seconds=0)
    extractor.client = Client()
    evidence = __import__("src.evidence_pack", fromlist=["EvidencePack"]).EvidencePack(company_domain="example.com")

    with pytest.raises(Exception, match="quota is exhausted"):
        extractor.extract(evidence)

    assert Interactions.calls == 1


def test_transient_429_uses_bounded_retries(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    class Interactions:
        calls = 0

        @classmethod
        def create(cls, **kwargs):
            cls.calls += 1
            if cls.calls < 3:
                raise RuntimeError("429 rate limited; retry shortly")
            return FakeInteraction()

    class Client:
        interactions = Interactions()

    extractor = GeminiExtractor(max_retries=2, retry_delay_seconds=0)
    extractor.client = Client()
    evidence = __import__("src.evidence_pack", fromlist=["EvidencePack"]).EvidencePack(company_domain="example.com")

    assert extractor.extract(evidence).company_domain == "example.com"
    assert Interactions.calls == 3
