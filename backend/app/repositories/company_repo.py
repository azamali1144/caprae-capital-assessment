import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Contact
from app.services.normalization.dedup import LeadCandidate

# on re-import only fill gaps, never overwrite what we already know
_FILL_ON_CONFLICT = (
    "industry",
    "city",
    "state",
    "country",
    "employee_count",
    "revenue_estimate",
)


def _company_row(c: LeadCandidate, job_id: uuid.UUID, source: str) -> dict:
    return {
        "id": uuid.uuid4(),
        "name": c.name,
        "name_normalized": c.name_normalized,
        "domain": c.domain,
        "website_url": f"https://{c.domain}" if c.domain else None,
        "industry": c.industry,
        "city": c.city,
        "state": c.state,
        "country": c.country,
        "employee_count": c.employees,
        "revenue_estimate": c.revenue,
        "source": source,
        "import_job_id": job_id,
    }


class CompanyRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def existing_domains(self, domains: list[str]) -> set[str]:
        if not domains:
            return set()
        rows = await self.session.scalars(select(Company.domain).where(Company.domain.in_(domains)))
        return set(rows)

    async def bulk_upsert(
        self, candidates: list[LeadCandidate], job_id: uuid.UUID, source: str
    ) -> list[uuid.UUID]:
        """Insert companies (+ their seed contacts). Returns company ids in order."""
        if not candidates:
            return []

        ids: list[uuid.UUID] = []
        for chunk_start in range(0, len(candidates), 500):
            chunk = candidates[chunk_start : chunk_start + 500]
            rows = [_company_row(c, job_id, source) for c in chunk]

            stmt = insert(Company).values(rows)
            excluded = stmt.excluded
            stmt = stmt.on_conflict_do_update(
                index_elements=[Company.domain],
                set_={
                    **{
                        col: func.coalesce(getattr(Company, col), getattr(excluded, col))
                        for col in _FILL_ON_CONFLICT
                    },
                    "import_job_id": excluded.import_job_id,
                    "updated_at": func.now(),
                },
            ).returning(Company.id, Company.domain)
            result = await self.session.execute(stmt)
            # returning() order isn't guaranteed, so match back by domain.
            # rows without a domain can't conflict, so they keep the id we generated
            by_domain = {domain: cid for cid, domain in result.all() if domain}
            chunk_ids = [by_domain.get(r["domain"], r["id"]) for r in rows]
            ids.extend(chunk_ids)

            await self._insert_contacts(zip(chunk_ids, chunk, strict=True))

        return ids

    async def _insert_contacts(self, pairs) -> None:
        rows = [
            {
                "id": uuid.uuid4(),
                "company_id": company_id,
                "full_name": seed.full_name,
                "title": seed.title,
                "email": seed.email.lower() if seed.email else None,
                "linkedin_url": seed.linkedin,
                "source": "csv",
                # raw phone for now, validation step normalises it to e164
                "phone_e164": seed.phone,
            }
            for company_id, cand in pairs
            for seed in cand.contacts
        ]
        if rows:
            stmt = insert(Contact).values(rows).on_conflict_do_nothing()
            await self.session.execute(stmt)

    async def count_for_job(self, job_id: uuid.UUID) -> int:
        return await self.session.scalar(
            select(func.count()).select_from(Company).where(Company.import_job_id == job_id)
        )
