import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str | None
    title: str | None
    email: str | None
    email_status: str
    email_type: str | None
    phone_e164: str | None
    phone_valid: bool
    linkedin_url: str | None
    is_decision_maker: bool
    source: str


class ScoreItem(BaseModel):
    rule: str
    points: int
    reason: str


class LeadOut(BaseModel):
    """Row in the leads table - kept small on purpose."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    domain: str | None
    website_url: str | None
    industry: str | None
    city: str | None
    state: str | None
    country: str | None
    employee_count: int | None
    score: int | None
    grade: str | None
    stage: str
    website_status: str | None
    last_enriched_at: datetime | None
    created_at: datetime
    best_contact: ContactOut | None = None
    contacts_count: int = 0
    top_reasons: list[str] = []


class LeadDetail(LeadOut):
    description: str | None
    founded_year: int | None
    copyright_year: int | None
    revenue_estimate: int | None
    tech_stack: list
    socials: dict
    signals: dict
    score_breakdown: list[ScoreItem]
    notes: str | None
    source: str
    import_job_id: uuid.UUID | None
    contacts: list[ContactOut] = []
