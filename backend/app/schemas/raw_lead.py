import re

from pydantic import BaseModel, field_validator

_NUM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([kmb])?", re.I)
_MULT = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def _parse_number(value) -> int | None:
    """'1,200' -> 1200, '$2.5M' -> 2500000, '11-50' -> 11 (lower bound)."""
    if value is None or value == "":
        return None
    if isinstance(value, int | float):
        return int(value)
    m = _NUM_RE.search(str(value).replace(",", ""))
    if not m:
        return None
    num = float(m.group(1)) * _MULT.get((m.group(2) or "").lower(), 1)
    return int(num)


class RawLead(BaseModel):
    """One row as it came in, before dedup/enrichment."""

    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    employees: int | None = None
    revenue: int | None = None
    owner: str | None = None
    title: str | None = None
    linkedin: str | None = None
    row_number: int | None = None

    @field_validator("*", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v == "" or v.lower() in {"n/a", "na", "none", "null", "-"}:
                return None
        return v

    @field_validator("employees", "revenue", mode="before")
    @classmethod
    def to_int(cls, v):
        return _parse_number(v)
