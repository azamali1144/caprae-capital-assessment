from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import SessionDep
from app.core.cache import cache_get_json, cache_set_json

router = APIRouter(tags=["stats"])

STATS_TTL = 30

# one round trip for everything the dashboard shows
STATS_SQL = text(
    """
    with lead_email as (
        select c.id,
               bool_or(ct.email_status = 'valid_mx') as has_valid,
               bool_or(ct.email is not null) as has_email
        from companies c
        left join contacts ct on ct.company_id = c.id
        group by c.id
    )
    select
        (select count(*) from companies) as total_leads,
        (select coalesce(sum(duplicates_removed), 0) from import_jobs) as duplicates_removed_total,
        (select count(*) from lead_email where has_valid) as leads_with_valid_email,
        (select count(*) from lead_email where has_email) as leads_with_email,
        (select round(avg(score)::numeric, 1) from companies where score is not null) as avg_score,
        (select count(*) from companies where last_enriched_at is not null) as enriched,
        (select coalesce(jsonb_object_agg(grade, n), '{}'::jsonb)
           from (select grade, count(*) n from companies where grade is not null group by grade) g
        ) as grades,
        (select coalesce(jsonb_object_agg(stage, n), '{}'::jsonb)
           from (select stage, count(*) n from companies group by stage) s
        ) as stages
    """
)


class StatsOut(BaseModel):
    total_leads: int
    duplicates_removed_total: int
    enriched: int
    leads_with_email: int
    valid_email_rate: float  # share of leads with at least one mx-valid email
    avg_score: float | None
    grade_distribution: dict[str, int]
    by_stage: dict[str, int]


@router.get("/stats", response_model=StatsOut)
async def get_stats(session: SessionDep):
    cached = await cache_get_json("stats:v1")
    if cached:
        return cached

    row = (await session.execute(STATS_SQL)).mappings().one()
    total = row["total_leads"] or 0
    out = StatsOut(
        total_leads=total,
        duplicates_removed_total=row["duplicates_removed_total"],
        enriched=row["enriched"],
        leads_with_email=row["leads_with_email"],
        valid_email_rate=round(row["leads_with_valid_email"] / total, 3) if total else 0.0,
        avg_score=float(row["avg_score"]) if row["avg_score"] is not None else None,
        grade_distribution={g: (row["grades"] or {}).get(g, 0) for g in "ABCD"},
        by_stage={
            s: (row["stages"] or {}).get(s, 0)
            for s in ("new", "qualified", "contacted", "disqualified")
        },
    )
    await cache_set_json("stats:v1", out.model_dump(), STATS_TTL)
    return out
