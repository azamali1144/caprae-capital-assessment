import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.import_job import ImportJob

STAGES = ("new", "qualified", "contacted", "disqualified")
WEBSITE_STATUSES = ("alive", "dead", "blocked", "timeout")


class Company(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(Text)
    name_normalized: Mapped[str] = mapped_column(Text, index=True)
    domain: Mapped[str | None] = mapped_column(Text, unique=True)
    website_url: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    employee_count: Mapped[int | None] = mapped_column(Integer)
    revenue_estimate: Mapped[int | None] = mapped_column(BigInteger)
    description: Mapped[str | None] = mapped_column(Text)
    founded_year: Mapped[int | None] = mapped_column(Integer)
    copyright_year: Mapped[int | None] = mapped_column(Integer)

    tech_stack: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    socials: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    signals: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    website_status: Mapped[str | None] = mapped_column(String(16))

    score: Mapped[int | None] = mapped_column(Integer)
    grade: Mapped[str | None] = mapped_column(String(1))
    score_breakdown: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    stage: Mapped[str] = mapped_column(String(16), default="new", server_default="new")
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), default="csv", server_default="csv")

    import_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_jobs.id", ondelete="SET NULL")
    )
    last_enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", lazy="selectin"
    )
    import_job: Mapped["ImportJob | None"] = relationship(back_populates="companies")

    __table_args__ = (
        CheckConstraint(f"stage IN {STAGES}", name="stage"),
        CheckConstraint(f"website_status IN {WEBSITE_STATUSES}", name="website_status"),
        CheckConstraint("grade IN ('A', 'B', 'C', 'D')", name="grade"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        # matches the default "score desc nulls last, id" ordering so paging uses the index
        Index("ix_companies_score_id", score.desc().nulls_last(), "id"),
        Index("ix_companies_stage", "stage"),
        Index("ix_companies_country_industry", "country", "industry"),
        Index("ix_companies_import_job_id", "import_job_id"),
    )

    def __repr__(self) -> str:
        return f"<Company {self.domain or self.name}>"
