from src.evidence_pack import EvidencePack
from src.llm import LLMExtractor
from src.models import LeadProfile


class FakeLLMExtractor(LLMExtractor):
    def extract(self, evidence: EvidencePack) -> LeadProfile:
        return LeadProfile(
            company_domain=evidence.company_domain,
            company_overview="Test overview.",
            icp="Test audience.",
            confidence=0.8,
        )


def test_llm_extractor_contract():
    evidence = EvidencePack(company_domain="example.com")
    extractor = FakeLLMExtractor()

    result = extractor.extract(evidence)

    assert isinstance(result, LeadProfile)
    assert result.company_domain == "example.com"
    assert result.confidence == 0.8