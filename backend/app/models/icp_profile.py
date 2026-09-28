from sqlalchemy import Boolean, CheckConstraint, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class IcpProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "icp_profiles"

    name: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(16), default="sales", server_default="sales")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # industries, countries, employee_min/max, min_years_in_business, tech_include, weights
    rules: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    __table_args__ = (CheckConstraint("mode IN ('sales', 'acquisition')", name="mode"),)
