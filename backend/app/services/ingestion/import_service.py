from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportJob
from app.repositories.company_repo import CompanyRepo
from app.repositories.import_repo import ImportRepo
from app.schemas.raw_lead import RawLead
from app.services.ingestion.csv_parser import parse_csv, parse_domain_list
from app.services.normalization.dedup import dedupe_leads
from app.services.normalization.domain import canonical_domain


@dataclass
class ImportResult:
    job: ImportJob
    unmapped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


async def _persist(
    session: AsyncSession, leads: list[RawLead], source: str, filename: str | None
) -> ImportJob:
    companies = CompanyRepo(session)
    jobs = ImportRepo(session)

    domains = [d for d in (canonical_domain(lead.domain) for lead in leads) if d]
    existing = await companies.existing_domains(domains)
    unique, removed = dedupe_leads(leads, existing_domains=existing)

    job = await jobs.create(
        source=source,
        filename=filename,
        status="running",
        total_rows=len(leads),
        duplicates_removed=removed,
        started_at=datetime.now(UTC),
    )
    await companies.bulk_upsert(unique, job.id, source)

    # enrichment isn't wired yet - for now the job is done once rows are saved
    job.processed = len(unique)
    job.status = "completed"
    job.finished_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(job)
    return job


async def import_csv(session: AsyncSession, data: bytes, filename: str | None) -> ImportResult:
    parsed = parse_csv(data)
    fields = set(parsed.mapping.values())
    source = "saasquatch_csv" if {"owner", "email", "industry"} <= fields else "csv"
    job = await _persist(session, parsed.leads, source, filename)
    return ImportResult(job=job, unmapped=parsed.unmapped, warnings=parsed.warnings)


async def import_domains(session: AsyncSession, domains: list[str]) -> ImportResult:
    leads = parse_domain_list(domains)
    bad = [lead.domain for lead in leads if not canonical_domain(lead.domain)]
    leads = [lead for lead in leads if canonical_domain(lead.domain)]
    warnings = [f"Skipped {len(bad)} entries that aren't valid domains."] if bad else []
    job = await _persist(session, leads, "domain_list", None)
    return ImportResult(job=job, warnings=warnings)
