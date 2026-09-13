from dataclasses import dataclass, field
import os


@dataclass
class UsageRecord:
    provider: str
    model: str
    domain: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    error: str | None = None


@dataclass
class UsageTracker:
    """Collects per-domain Gemini usage records and non-fatal errors."""

    records: list[UsageRecord] = field(default_factory=list)

    @staticmethod
    def estimated_gemini_cost(
        input_tokens: int,
        output_tokens: int,
        thought_tokens: int = 0,
    ) -> float:
        """Estimate cost from explicit environment pricing, never guesses.

        Gemini pricing changes by model, region, and account. Users can set
        the three per-million-token rates in ``.env`` for the model they run;
        absent rates intentionally produce 0.0 rather than a misleading cost.
        """
        def rate(name: str) -> float:
            try:
                return max(0.0, float(os.getenv(name, "0")))
            except ValueError:
                return 0.0

        return round(
            input_tokens * rate("GEMINI_INPUT_USD_PER_1M_TOKENS") / 1_000_000
            + output_tokens * rate("GEMINI_OUTPUT_USD_PER_1M_TOKENS") / 1_000_000
            + thought_tokens * rate("GEMINI_THOUGHT_USD_PER_1M_TOKENS") / 1_000_000,
            8,
        )

    def add(self, provider: str, model: str, input_tokens: int = 0,
            output_tokens: int = 0, thought_tokens: int = 0,
            total_tokens: int | None = None, estimated_cost_usd: float = 0.0,
            domain: str = "") -> UsageRecord:
        total = total_tokens if total_tokens is not None else input_tokens + output_tokens + thought_tokens
        record = UsageRecord(provider=provider, model=model, domain=domain,
                             input_tokens=max(0, input_tokens), output_tokens=max(0, output_tokens),
                             thought_tokens=max(0, thought_tokens), total_tokens=max(0, total),
                             estimated_cost_usd=max(0.0, estimated_cost_usd))
        self.records.append(record)
        return record

    def record_error(self, provider: str, model: str, error: str, domain: str = "") -> None:
        self.records.append(UsageRecord(provider=provider, model=model, domain=domain, error=error))

    def summary(self, domain: str | None = None, start: int = 0) -> dict:
        records = self.records[start:]
        if domain is not None:
            records = [record for record in records if record.domain == domain]
        return {
            "provider": records[-1].provider if records else "gemini",
            "model": records[-1].model if records else "",
            "llm_calls": sum(record.error is None for record in records),
            "input_tokens": sum(record.input_tokens for record in records),
            "output_tokens": sum(record.output_tokens for record in records),
            "thought_tokens": sum(record.thought_tokens for record in records),
            "total_tokens": sum(record.total_tokens for record in records),
            "estimated_cost_usd": round(sum(record.estimated_cost_usd for record in records), 8),
            "errors": [record.error for record in records if record.error],
        }
