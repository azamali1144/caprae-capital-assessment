import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models import Company, ImportJob
from app.repositories.icp_repo import IcpRepo
from app.services.enrichment.apply import apply_company_fields, merge_contacts, validate_contacts
from app.services.enrichment.service import enrich_domain
from app.services.scoring.service import icp_dict, score_one

log = logging.getLogger(__name__)


async def _bump(job_id: uuid.UUID, processed: int = 0, failed: int = 0) -> None:
    # atomic counter update so concurrent workers don't stomp each other
    async with SessionLocal() as session:
        await session.execute(
            update(ImportJob)
            .where(ImportJob.id == job_id)
            .values(processed=ImportJob.processed + processed, failed=ImportJob.failed + failed)
        )
        await session.commit()


async def process_company(company_id: uuid.UUID, icp: dict, force: bool = False) -> None:
    """enrich -> validate -> score for a single company, in its own session."""
    async with SessionLocal() as session:
        company = await session.scalar(
            select(Company).options(selectinload(Company.contacts)).where(Company.id == company_id)
        )
        if company is None:
            return

        if company.domain:
            enrichment = await enrich_domain(company.domain, company.country, force=force)
            apply_company_fields(company, enrichment)
            merge_contacts(company, enrichment)

        await validate_contacts(company)
        score_one(company, icp)
        await session.commit()


async def run_import_job(job_id: uuid.UUID) -> None:
    settings = get_settings()
    started = time.perf_counter()

    async with SessionLocal() as session:
        job = await session.get(ImportJob, job_id)
        if job is None:
            return
        job.status = "running"
        job.started_at = job.started_at or datetime.now(UTC)
        await session.commit()

        icp = icp_dict(await IcpRepo(session).active())
        company_ids = list(
            await session.scalars(select(Company.id).where(Company.import_job_id == job_id))
        )

    sem = asyncio.Semaphore(settings.crawl_concurrency)

    async def worker(cid: uuid.UUID) -> None:
        async with sem:
            try:
                await process_company(cid, icp)
                await _bump(job_id, processed=1)
            except Exception as exc:  # one bad site shouldn't kill the whole import
                log.warning("enrichment failed for company %s: %s", cid, exc)
                await _bump(job_id, failed=1)

    try:
        await asyncio.gather(*(worker(cid) for cid in company_ids))
        status, error = "completed", None
    except Exception as exc:
        log.exception("import job %s crashed", job_id)
        status, error = "failed", str(exc)[:500]

    async with SessionLocal() as session:
        await session.execute(
            update(ImportJob)
            .where(ImportJob.id == job_id)
            .values(status=status, error=error, finished_at=datetime.now(UTC))
        )
        await session.commit()

    log.info(
        "import %s: %d companies in %.1fs (%s)",
        job_id,
        len(company_ids),
        time.perf_counter() - started,
        status,
    )
