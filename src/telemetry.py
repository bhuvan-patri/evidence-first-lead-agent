from dataclasses import dataclass, field


@dataclass
class UsageRecord:
    """
    Records LLM usage for a single enrichment operation.
    """

    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class UsageTracker:
    """
    Collects LLM usage records across domains.
    """

    records: list[UsageRecord] = field(default_factory=list)

    def add(
        self,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        thought_tokens: int = 0,
        total_tokens: int | None = None,
        estimated_cost_usd: float = 0.0,
    ) -> UsageRecord:
        if total_tokens is None:
            total_tokens = (
                input_tokens
                + output_tokens
                + thought_tokens
            )

        record = UsageRecord(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thought_tokens=thought_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )

        self.records.append(record)

        return record

    @property
    def total_input_tokens(self) -> int:
        return sum(
            record.input_tokens
            for record in self.records
        )

    @property
    def total_output_tokens(self) -> int:
        return sum(
            record.output_tokens
            for record in self.records
        )

    @property
    def total_thought_tokens(self) -> int:
        return sum(
            record.thought_tokens
            for record in self.records
        )

    @property
    def total_tokens(self) -> int:
        return sum(
            record.total_tokens
            for record in self.records
        )

    @property
    def total_estimated_cost_usd(self) -> float:
        return round(
            sum(
                record.estimated_cost_usd
                for record in self.records
            ),
            8,
        )

    def summary(self) -> dict:
        return {
            "llm_calls": len(self.records),
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "thought_tokens": self.total_thought_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.total_estimated_cost_usd,
        }