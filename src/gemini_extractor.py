"""Gemini Interactions API extraction with bounded transient retries."""

from __future__ import annotations

import os
import time

from dotenv import load_dotenv
from google import genai
from pydantic import ValidationError

from src.evidence_pack import EvidencePack
from src.llm import LLMExtractor
from src.models import LeadProfileDraft
from src.telemetry import UsageTracker

load_dotenv()

DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"


class GeminiExtractionError(RuntimeError):
    """A non-fabricated extraction failure that can be reported per domain."""


class GeminiExtractor(LLMExtractor):
    def __init__(self, model: str | None = None, usage_tracker: UsageTracker | None = None,
                 max_retries: int = 2, retry_delay_seconds: float = 1.0):
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        self.usage_tracker = usage_tracker
        self.max_retries = max(0, max_retries)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)
        api_key = os.getenv("GEMINI_API_KEY")
        # This project uses a Gemini Developer API key, never Vertex/Enterprise
        # OAuth credentials.  The SDK otherwise leaves ``vertexai`` unset and
        # can select a different authentication mode from ambient environment
        # variables in an IDE or shell.
        self.client = genai.Client(api_key=api_key, vertexai=False) if api_key else None

    def extract(self, evidence: EvidencePack) -> LeadProfileDraft:
        if self.client is None:
            message = "GEMINI_API_KEY is not configured; Gemini extraction was not attempted."
            self._record_error(message, evidence.company_domain)
            raise GeminiExtractionError(message)
        prompt = self._prompt(evidence)
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                interaction = self.client.interactions.create(
                    model=self.model,
                    input=prompt,
                    response_format={"type": "text", "mime_type": "application/json",
                                     "schema": LeadProfileDraft.model_json_schema()},
                )
                output = getattr(interaction, "output_text", None)
                if not output:
                    raise GeminiExtractionError("Gemini returned no structured result.")
                draft = LeadProfileDraft.model_validate_json(output)
                draft.company_domain = evidence.company_domain
                self._record_usage(interaction, evidence.company_domain)
                return draft
            except (ValidationError, ValueError) as exc:
                message = f"Gemini returned invalid structured data: {exc}"
                self._record_error(message, evidence.company_domain)
                raise GeminiExtractionError(message) from exc
            except Exception as exc:
                last_error = exc
                if self._is_quota_exhausted(exc):
                    break
                if attempt >= self.max_retries or not self._is_transient(exc):
                    break
                time.sleep(self.retry_delay_seconds * (2 ** attempt))
        attempts = attempt + 1
        reason = "Gemini quota is exhausted; no retry was attempted." if self._is_quota_exhausted(last_error) else "Gemini extraction failed."
        message = f"{reason} Attempts: {attempts}. {type(last_error).__name__}: {last_error}"
        self._record_error(message, evidence.company_domain)
        raise GeminiExtractionError(message) from last_error

    def _prompt(self, evidence: EvidencePack) -> str:
        return f"""You extract a public company lead profile from an evidence pack.
Use ONLY supplied evidence. Never invent names, roles, emails, URLs, company facts, or audience claims. Leave unsupported fields empty.
Write exactly a concise two-sentence company_overview when overview evidence permits; otherwise return an empty string.
Identify ICP only from explicit target-audience evidence. Extract only public generic/business email addresses.
Leadership requires strong company/team/leadership context. Never treat people in testimonials, customer stories, case studies, reviews, or customer quotes as company leadership.
Never use pricing/plan/free-trial text as overview. LinkedIn URLs must be explicitly present in evidence. Do not output confidence.

Company domain: {evidence.company_domain}

Curated evidence:
{evidence.to_text()}"""

    @staticmethod
    def _is_transient(error: Exception) -> bool:
        text = str(error).lower()
        return any(marker in text for marker in ("429", "resource exhausted", "500", "502", "503", "504", "timeout", "connection", "network"))

    @staticmethod
    def _is_quota_exhausted(error: Exception | None) -> bool:
        """Daily/request quota exhaustion is not a rate-limit worth retrying."""
        if error is None:
            return False
        details = " ".join(
            str(value) for value in (
                error,
                getattr(error, "code", ""),
                getattr(error, "status_code", ""),
                getattr(getattr(error, "response", None), "text", ""),
            )
        ).lower()
        return any(marker in details for marker in (
            "generate_content_free_tier_requests",
            "quota exceeded",
            "current quota",
            "daily quota",
            "request quota",
            "quota exhausted",
        ))

    def _record_error(self, message: str, domain: str) -> None:
        if self.usage_tracker:
            self.usage_tracker.record_error("gemini", self.model, message, domain)

    def _record_usage(self, interaction, domain: str) -> None:
        if not self.usage_tracker:
            return
        usage = getattr(interaction, "usage", None) or getattr(interaction, "usage_metadata", None)
        if usage is None:
            self.usage_tracker.add("gemini", self.model, domain=domain)
            return
        def count(*names: str) -> int:
            for name in names:
                value = getattr(usage, name, None)
                if value is not None:
                    try:
                        return int(value)
                    except (TypeError, ValueError):
                        return 0
            return 0
        input_tokens = count("total_input_tokens", "prompt_token_count")
        output_tokens = count("total_output_tokens", "candidates_token_count")
        thought_tokens = count("total_thought_tokens", "thoughts_token_count")
        self.usage_tracker.add(
            "gemini", self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thought_tokens=thought_tokens,
            total_tokens=count("total_tokens", "total_token_count"),
            estimated_cost_usd=UsageTracker.estimated_gemini_cost(
                input_tokens, output_tokens, thought_tokens
            ),
            domain=domain,
        )
