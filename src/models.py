"""Validated public data contracts for the enrichment pipeline."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


GENERIC_EMAIL_PREFIXES = {
    "info", "hello", "sales", "support", "contact", "help", "press",
    "media", "partnerships", "partners", "legal", "security", "privacy",
}

EMAIL_PATTERN = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)


def normalize_generic_email(value: object) -> str | None:
    """Return a normalized public-role inbox, or ``None`` for other addresses.

    Keeping this rule in one place prevents page planning, evidence collection,
    and Pydantic validation from disagreeing about what counts as a contact
    point for this assignment.
    """
    email = str(value or "").strip().lower()
    if not EMAIL_PATTERN.fullmatch(email):
        return None
    return email if email.split("@", 1)[0] in GENERIC_EMAIL_PREFIXES else None


class LeadershipPerson(BaseModel):
    name: str = ""
    role: str = ""
    linkedin_url: str | None = None

    @field_validator("name", "role", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, value: str | None) -> str | None:
        if not value:
            return None
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc.endswith("linkedin.com"):
            raise ValueError("linkedin_url must be an HTTP(S) LinkedIn URL")
        return value


class Evidence(BaseModel):
    field: str
    value: str
    source_url: str
    source_type: str
    strength: str = "medium"


class Telemetry(BaseModel):
    provider: str = "gemini"
    model: str = ""
    llm_calls: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    thought_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    errors: list[str] = Field(default_factory=list)


class LeadProfileDraft(BaseModel):
    company_domain: str
    company_overview: str = ""
    icp: str = ""
    generic_emails: list[str] = Field(default_factory=list)
    leadership: list[LeadershipPerson] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    @field_validator("company_domain", "company_overview", "icp", mode="before")
    @classmethod
    def normalize_strings(cls, value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @field_validator("generic_emails", mode="before")
    @classmethod
    def validate_generic_emails(cls, values: object) -> list[str]:
        if not values:
            return []
        result: list[str] = []
        for value in values:
            email = normalize_generic_email(value)
            if email is None:
                continue
            if email not in result:
                result.append(email)
        return result

    @model_validator(mode="after")
    def deduplicate_leadership(self) -> "LeadProfileDraft":
        seen: set[tuple[str, str]] = set()
        unique: list[LeadershipPerson] = []
        for person in self.leadership:
            key = (person.name.casefold(), person.role.casefold())
            if not person.name or not person.role or key in seen:
                continue
            seen.add(key)
            unique.append(person)
        self.leadership = unique
        return self


class LeadProfile(LeadProfileDraft):
    confidence: float = Field(ge=0.0, le=1.0)
    telemetry: Telemetry = Field(default_factory=Telemetry)
