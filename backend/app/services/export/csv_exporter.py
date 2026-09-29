import csv
import io
from collections.abc import AsyncIterator

from sqlalchemy.orm import selectinload

from app.core.db import SessionLocal
from app.models import Company
from app.repositories.lead_query import filtered, ordered
from app.schemas.common import LeadFilters
from app.services.leads.presenter import best_contact, top_reasons

# column names hubspot/salesforce/pipedrive importers pick up without manual mapping
HEADERS = [
    "Company Name",
    "Domain",
    "Website",
    "Score",
    "Grade",
    "Top Reasons",
    "Contact Name",
    "Title",
    "Email",
    "Email Status",
    "Phone",
    "LinkedIn",
    "Industry",
    "City",
    "State",
    "Country",
    "Employees",
    "Founded",
    "Stage",
    "Notes",
]

BATCH = 500


def _row(c: Company) -> list:
    contact = best_contact(c.contacts)
    return [
        c.name,
        c.domain or "",
        c.website_url or "",
        c.score if c.score is not None else "",
        c.grade or "",
        "; ".join(top_reasons(c, n=3)),
        (contact.full_name if contact else "") or "",
        (contact.title if contact else "") or "",
        (contact.email if contact else "") or "",
        contact.email_status if contact and contact.email else "",
        (contact.phone_e164 if contact else "") or "",
        (contact.linkedin_url if contact else "") or c.socials.get("linkedin", ""),
        c.industry or "",
        c.city or "",
        c.state or "",
        c.country or "",
        c.employee_count if c.employee_count is not None else "",
        c.founded_year or "",
        c.stage,
        c.notes or "",
    ]


def _line(values: list) -> str:
    buf = io.StringIO()
    csv.writer(buf).writerow(values)
    return buf.getvalue()


async def stream_csv(filters: LeadFilters, ids: list | None = None) -> AsyncIterator[str]:
    """Yields the csv a chunk at a time so a 5k-lead export never sits in memory.

    Opens its own session - the request one is gone by the time the body streams.
    """
    yield "\ufeff" + _line(HEADERS)  # bom so excel opens utf-8 properly

    stmt = ordered(filtered(filters), filters).options(selectinload(Company.contacts))
    if ids:
        stmt = stmt.where(Company.id.in_(ids))

    offset = 0
    async with SessionLocal() as session:
        while True:
            rows = list(await session.scalars(stmt.offset(offset).limit(BATCH)))
            if not rows:
                break
            yield "".join(_line(_row(c)) for c in rows)
            offset += BATCH
