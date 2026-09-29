from sqlalchemy import Select, and_, exists, func, literal_column, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Company, Contact
from app.schemas.common import LeadFilters, Pagination

# has to match the expression in the gin index migration, otherwise postgres won't use it
# (written as raw sql so no bind params sneak in and break the match)
_SEARCH_DOC = literal_column(
    "to_tsvector('simple', companies.name || ' ' || coalesce(companies.description, ''))"
)


def filtered(filters: LeadFilters) -> Select:
    stmt = select(Company)
    conds = []

    if filters.q:
        q = filters.q.strip()
        conds.append(
            or_(
                _SEARCH_DOC.op("@@")(func.plainto_tsquery("simple", q)),
                Company.name.ilike(f"%{q}%"),
                Company.domain.ilike(f"%{q}%"),
            )
        )
    if filters.grade:
        conds.append(Company.grade.in_(filters.grade))
    if filters.min_score is not None:
        conds.append(Company.score >= filters.min_score)
    if filters.industry:
        conds.append(Company.industry.ilike(f"%{filters.industry.strip()}%"))
    if filters.country:
        conds.append(func.lower(Company.country) == filters.country.strip().lower())
    if filters.stage:
        conds.append(Company.stage == filters.stage)
    if filters.email_status:
        conds.append(
            exists().where(
                and_(Contact.company_id == Company.id, Contact.email_status == filters.email_status)
            )
        )
    if filters.import_id:
        conds.append(Company.import_job_id == filters.import_id)

    if conds:
        stmt = stmt.where(*conds)
    return stmt


def ordered(stmt: Select, filters: LeadFilters) -> Select:
    col = getattr(Company, filters.sort)
    col = col.asc() if filters.order == "asc" else col.desc()
    # nulls (not scored yet) at the bottom, id as tie-breaker so paging is stable
    return stmt.order_by(col.nulls_last(), Company.id)


async def list_leads(
    session: AsyncSession, filters: LeadFilters, paging: Pagination
) -> tuple[list[Company], int]:
    base = filtered(filters)
    total = await session.scalar(select(func.count()).select_from(base.subquery()))

    stmt = (
        ordered(base, filters)
        .options(selectinload(Company.contacts))
        .offset((paging.page - 1) * paging.page_size)
        .limit(paging.page_size)
    )
    rows = list(await session.scalars(stmt))
    return rows, total or 0
