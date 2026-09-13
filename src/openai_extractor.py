import os

from dotenv import load_dotenv
from openai import OpenAI

from src.evidence_pack import EvidencePack
from src.llm import LLMExtractor
from src.models import LeadProfile


load_dotenv()


class OpenAIExtractor(LLMExtractor):
    def __init__(self, model: str = "gpt-5-mini"):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract(self, evidence: EvidencePack) -> LeadProfile:
        evidence_text = evidence.to_text()

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a lead-enrichment extraction engine. "
                        "Extract information only from the supplied evidence. "
                        "Never invent, guess, or infer specific people, emails, "
                        "or URLs that are not supported by the evidence. "
                        "If information is unavailable, return an empty value. "
                        "Return the result using the required structured schema."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company domain: {evidence.company_domain}\n\n"
                        "Evidence:\n"
                        f"{evidence_text}"
                    ),
                },
            ],
            text_format=LeadProfile,
        )

        result = response.output_parsed

        if result is None:
            raise ValueError("LLM returned no structured result.")

        return result