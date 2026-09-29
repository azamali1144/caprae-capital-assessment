from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.deps import SessionDep
from app.repositories.lead_query import list_leads
from app.schemas.common import LeadFilters, Page, Pagination
from app.schemas.company import LeadOut
from app.services.leads.presenter import to_lead_out

router = APIRouter(prefix="/leads", tags=["leads"])


def lead_filters(
    q: str | None = None,
    grade: Annotated[list[str], Query()] = [],  # noqa: B006 - fastapi copies it
    min_score: int | None = None,
    industry: str | None = None,
    country: str | None = None,
    stage: str | None = None,
    email_status: str | None = None,
    import_id: str | None = Query(default=None, alias="import"),
    sort: str = "score",
    order: str = "desc",
) -> LeadFilters:
    try:
        return LeadFilters(
            q=q,
            grade=grade,
            min_score=min_score,
            industry=industry,
            country=country,
            stage=stage,
            email_status=email_status,
            import_id=import_id or None,
            sort=sort,
            order=order,
        )
    except ValidationError as exc:
        # surface as a normal 422 instead of a 500
        raise RequestValidationError(exc.errors()) from exc


FiltersDep = Annotated[LeadFilters, Depends(lead_filters)]


@router.get("", response_model=Page[LeadOut])
async def get_leads(
    session: SessionDep,
    filters: FiltersDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    paging = Pagination(page=page, page_size=page_size)
    rows, total = await list_leads(session, filters, paging)
    return Page[LeadOut](
        items=[to_lead_out(c) for c in rows],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )
