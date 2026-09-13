from dataclasses import dataclass, field


@dataclass
class EvidenceItem:
    field: str
    value: str
    source_url: str
    source_type: str


@dataclass
class EvidencePack:
    company_domain: str
    items: list[EvidenceItem] = field(default_factory=list)

    def add(self, item: EvidenceItem) -> None:
        self.items.append(item)

    def for_goal(self, goal: str) -> list[EvidenceItem]:
        return [
            item
            for item in self.items
            if item.field == goal
        ]

    def to_text(self) -> str:
        sections = []

        for item in self.items:
            sections.append(
                f"[{item.field}] "
                f"{item.value}\n"
                f"Source: {item.source_url}\n"
                f"Type: {item.source_type}"
            )

        return "\n\n".join(sections)