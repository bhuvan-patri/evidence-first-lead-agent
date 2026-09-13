from pydantic import BaseModel, Field


class LeadershipPerson(BaseModel):
    name: str
    role: str
    linkedin_url: str | None = None


class Evidence(BaseModel):
    field: str
    value: str
    source_url: str
    source_type: str


class LeadProfileDraft(BaseModel):
    company_domain: str
    company_overview: str
    icp: str
    generic_emails: list[str] = Field(default_factory=list)
    leadership: list[LeadershipPerson] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class LeadProfile(LeadProfileDraft):
    confidence: float = Field(ge=0.0, le=1.0)