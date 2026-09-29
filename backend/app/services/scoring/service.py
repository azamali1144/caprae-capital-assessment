import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Company, IcpProfile
from app.repositories.icp_repo import IcpRepo
from app.services.scoring.engine import ScoreResult, score_company

log = logging.getLogger(__name__)

RESCORE_BATCH = 500

DEFAULT_PROFILES = [
    {
        "name": "Default Sales ICP",
        "mode": "sales",
        "is_active": True,
        "rules": {
            "industries": ["HVAC", "Plumbing", "Electrical", "Roofing", "Landscaping"],
            "countries": ["US"],
            "employee_min": 5,
            "employee_max": 200,
        },
    },
    {
        "name": "Searcher - Acquisition Fit",
        "mode": "acquisition",
        "is_active": False,
        "rules": {
            "industries": ["HVAC", "Plumbing", "Electrical", "Roofing", "Landscaping"],
            "countries": ["US"],
            "employee_min": 5,
            "employee_max": 100,
            "min_years_in_business": 10,
        },
    },
]


def icp_dict(profile: IcpProfile | None) -> dict:
    if profile is None:
        return {"mode": "sales"}
    return {**(profile.rules or {}), "mode": profile.mode}


def apply_score(company: Company, result: ScoreResult) -> None:
    company.score = result.score
    company.grade = result.grade
    company.score_breakdown = result.breakdown


def score_one(company: Company, icp: dict) -> ScoreResult:
    result = score_company(company, company.contacts, icp)
    apply_score(company, result)
    return result


async def seed_default_profiles(session: AsyncSession) -> None:
    repo = IcpRepo(session)
    if await repo.count():
        return
    for p in DEFAULT_PROFILES:
        await repo.create(**p)
    await session.commit()
    log.info("seeded %d default icp profiles", len(DEFAULT_PROFILES))


async def rescore_all(session: AsyncSession, profile: IcpProfile) -> int:
    """Re-score every company against the profile, 500 at a time (keyset paging on id)."""
    icp = icp_dict(profile)
    total = 0
    last_id = None
    while True:
        stmt = (
            select(Company)
            .options(selectinload(Company.contacts))
            .order_by(Company.id)
            .limit(RESCORE_BATCH)
        )
        if last_id is not None:
            stmt = stmt.where(Company.id > last_id)
        batch = list(await session.scalars(stmt))
        if not batch:
            break
        for company in batch:
            score_one(company, icp)
        await session.commit()
        total += len(batch)
        last_id = batch[-1].id
    return total
