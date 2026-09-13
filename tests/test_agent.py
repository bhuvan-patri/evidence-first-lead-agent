from src.agent import LeadEnrichmentAgent
from src.models import LeadProfileDraft


class FakeAnalyzer:
    def analyze(self, domain):
        return {
            "domain": domain,
            "success": True,
            "pages_discovered": 3,
            "pages_selected": 2,
            "pages": [
                {
                    "url": f"https://{domain}/about",
                    "success": True,
                    "content": "We build software for developers.",
                }
            ],
        }


class FailingAnalyzer:
    def analyze(self, domain):
        raise RuntimeError("Simulated website failure")


class FakeExtractor:
    def extract(self, evidence):
        return LeadProfileDraft(
            company_domain=evidence.company_domain,
            company_overview="Example company builds software for developers.",
            icp="Software developers and engineering teams.",
            generic_emails=[],
            leadership=[],
        )


def test_agent_enriches_domain():
    agent = LeadEnrichmentAgent(
        llm_extractor=FakeExtractor()
    )

    agent.analyzer = FakeAnalyzer()

    result = agent.enrich_domain("example.com")

    assert result["success"] is True
    assert result["profile"] is not None
    assert result["profile"].company_domain == "example.com"


def test_agent_isolates_domain_failure():
    agent = LeadEnrichmentAgent(
        llm_extractor=FakeExtractor()
    )

    agent.analyzer = FailingAnalyzer()

    result = agent.enrich_domain("broken.example")

    assert result["success"] is False
    assert result["profile"] is None
    assert "Simulated website failure" in result["error"]


def test_agent_continues_after_domain_failure():
    class SelectiveAnalyzer:
        def analyze(self, domain):
            if domain == "broken.example":
                raise RuntimeError("Simulated failure")

            return {
                "domain": domain,
                "success": True,
                "pages_discovered": 1,
                "pages_selected": 1,
                "pages": [
                    {
                        "url": f"https://{domain}/",
                        "success": True,
                        "content": "We build software for developers.",
                    }
                ],
            }

    agent = LeadEnrichmentAgent(
        llm_extractor=FakeExtractor()
    )

    agent.analyzer = SelectiveAnalyzer()

    results = agent.enrich_domains(
        [
            "broken.example",
            "working.example",
        ]
    )

    assert len(results) == 2
    assert results[0]["success"] is False
    assert results[1]["success"] is True
