import os

from dotenv import load_dotenv
from google import genai

from src.evidence_pack import EvidencePack
from src.llm import LLMExtractor
from src.models import LeadProfileDraft
from src.telemetry import UsageTracker


load_dotenv()


class GeminiExtractor(LLMExtractor):
    def __init__(
        self,
        model: str = "gemini-3.6-flash",
        usage_tracker: UsageTracker | None = None,
    ):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = model
        self.usage_tracker = usage_tracker

    def extract(
        self,
        evidence: EvidencePack,
    ) -> LeadProfileDraft:
        evidence_text = evidence.to_text()

        prompt = f"""
You are a lead-enrichment extraction engine.

Extract information ONLY from the supplied evidence.

Rules:
- Never invent or guess information.
- Do not create people, roles, emails, or LinkedIn URLs
  that are not supported by the evidence.
- If information is unavailable, return an empty value
  or empty list.
- Keep the company overview to approximately two sentences.
- Identify the company's likely target audience from the evidence.
- Return only information supported by the evidence.
- Do not calculate or provide a confidence score.

Company domain:
{evidence.company_domain}

Evidence:
{evidence_text}
"""

        interaction = self.client.interactions.create(
            model=self.model,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": LeadProfileDraft.model_json_schema(),
            },
        )

        if not interaction.output_text:
            raise ValueError(
                "Gemini returned no structured result."
            )

        self._record_usage(interaction)

        return LeadProfileDraft.model_validate_json(
            interaction.output_text
        )

    def _record_usage(self, interaction) -> None:
        if self.usage_tracker is None:
            return

        usage = getattr(
            interaction,
            "usage",
            None,
        )

        if usage is None:
            return

        input_tokens = self._get_token_count(
            usage,
            "total_input_tokens",
        )

        output_tokens = self._get_token_count(
            usage,
            "total_output_tokens",
        )

        thought_tokens = self._get_token_count(
            usage,
            "total_thought_tokens",
        )

        total_tokens = self._get_token_count(
            usage,
            "total_tokens",
        )

        self.usage_tracker.add(
            provider="gemini",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thought_tokens=thought_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=0.0,
        )

    @staticmethod
    def _get_token_count(
        usage,
        attribute: str,
    ) -> int:
        value = getattr(
            usage,
            attribute,
            0,
        )

        if value is None:
            return 0

        try:
            return int(value)
        except (TypeError, ValueError):
            return 0