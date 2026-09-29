import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SORT_FIELDS = ("score", "name", "created_at", "last_enriched_at", "employee_count", "founded_year")


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class LeadFilters(BaseModel):
    """Shared by GET /leads and GET /exports/csv so the export matches what you see."""

    q: str | None = None
    grade: list[Literal["A", "B", "C", "D"]] = []
    min_score: int | None = Field(default=None, ge=0, le=100)
    industry: str | None = None
    country: str | None = None
    stage: str | None = None
    email_status: str | None = None
    import_id: uuid.UUID | None = None
    sort: Literal[SORT_FIELDS] = "score"  # type: ignore[valid-type]
    order: Literal["asc", "desc"] = "desc"

    @field_validator("grade", mode="before")
    @classmethod
    def split_grades(cls, v):
        # ?grade=A,B and ?grade=A&grade=B both work
        if isinstance(v, str):
            v = [v]
        out = []
        for item in v or []:
            out.extend(g.strip().upper() for g in str(item).split(",") if g.strip())
        return out


class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
