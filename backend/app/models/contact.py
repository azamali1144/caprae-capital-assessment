import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company

EMAIL_STATUSES = ("valid_mx", "no_mx", "invalid_syntax", "disposable", "unknown")


class Contact(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "contacts"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    full_name: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    email_status: Mapped[str] = mapped_column(
        String(16), default="unknown", server_default="unknown"
    )
    email_type: Mapped[str | None] = mapped_column(String(16))  # personal | role
    phone_e164: Mapped[str | None] = mapped_column(String(32))
    phone_valid: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    is_decision_maker: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    source: Mapped[str] = mapped_column(String(16), default="csv", server_default="csv")

    company: Mapped["Company"] = relationship(back_populates="contacts")

    __table_args__ = (
        UniqueConstraint("company_id", "email", name="uq_contacts_company_email"),
        # backs the "has a verified email" filter on the leads list
        Index("ix_contacts_company_status", "company_id", "email_status"),
        CheckConstraint(f"email_status IN {EMAIL_STATUSES}", name="email_status"),
        CheckConstraint("email_type IN ('personal', 'role')", name="email_type"),
    )
