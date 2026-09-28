from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company

JOB_STATUSES = ("queued", "running", "completed", "failed")


class ImportJob(UUIDMixin, Base):
    __tablename__ = "import_jobs"

    source: Mapped[str] = mapped_column(String(32))  # saasquatch_csv | csv | domain_list
    filename: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="queued", server_default="queued")

    total_rows: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    duplicates_removed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    processed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    companies: Mapped[list["Company"]] = relationship(back_populates="import_job")

    __table_args__ = (CheckConstraint(f"status IN {JOB_STATUSES}", name="status"),)
