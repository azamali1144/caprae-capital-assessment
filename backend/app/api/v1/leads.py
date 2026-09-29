import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core.errors import NotFound
from app.models import Company
from app.repositories.icp_repo import IcpRepo
from app.repositories.lead_query import list_leads
from app.schemas.common import LeadFilters, Page, Pagination
from app.schemas.company import LeadDetail, LeadOut
from app.schemas.lead_actions import BulkAction, BulkResult, LeadUpdate
from app.services.jobs.enrich_job import process_company
from app.services.leads.presenter import to_lead_detail, to_lead_out
from app.services.scoring.service import icp_dict

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


async def _load(session, lead_id: uuid.UUID) -> Company:
    company = await session.scalar(
        select(Company)
        .options(selectinload(Company.contacts))
        .where(Company.id == lead_id)
        .execution_options(populate_existing=True)
    )
    if not company:
        raise NotFound("Lead")
    return company


@router.get("/{lead_id}", response_model=LeadDetail)
async def get_lead(lead_id: uuid.UUID, session: SessionDep):
    return to_lead_detail(await _load(session, lead_id))


@router.patch("/{lead_id}", response_model=LeadDetail)
async def update_lead(lead_id: uuid.UUID, body: LeadUpdate, session: SessionDep):
    company = await _load(session, lead_id)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(company, field, value)
    await session.commit()
    return to_lead_detail(await _load(session, lead_id))


@router.post("/bulk", response_model=BulkResult)
async def bulk_action(body: BulkAction, session: SessionDep, tasks: BackgroundTasks):
    ids = list(dict.fromkeys(body.ids))

    if body.action == "set_stage":
        res = await session.execute(
            update(Company).where(Company.id.in_(ids)).values(stage=body.value)
        )
        await session.commit()
        return BulkResult(action=body.action, affected=res.rowcount)

    if body.action == "delete":
        # contacts go with it (fk on delete cascade) - this is also our gdpr "forget me"
        res = await session.execute(delete(Company).where(Company.id.in_(ids)))
        await session.commit()
        return BulkResult(action=body.action, affected=res.rowcount)

    icp = icp_dict(await IcpRepo(session).active())
    found = list(await session.scalars(select(Company.id).where(Company.id.in_(ids))))
    for cid in found:
        tasks.add_task(process_company, cid, icp, True)
    return BulkResult(action=body.action, affected=len(found))


@router.post("/{lead_id}/enrich", response_model=LeadDetail, status_code=status.HTTP_200_OK)
async def re_enrich(lead_id: uuid.UUID, session: SessionDep, force: bool = True):
    await _load(session, lead_id)  # 404 early
    icp = icp_dict(await IcpRepo(session).active())
    # single lead is quick enough (a few seconds) to do inline, so the drawer updates right away
    await process_company(lead_id, icp, force=force)
    return to_lead_detail(await _load(session, lead_id))
