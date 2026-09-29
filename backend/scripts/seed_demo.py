"""Load data/sample_leads.csv and run the full enrich -> validate -> score job.

    cd backend && uv run python -m scripts.seed_demo [path/to/file.csv]

Handy for a fresh database or a demo deploy, so there's something to look at.
Takes about a minute (it really crawls the sites).
"""

import asyncio
import sys
import time
from pathlib import Path

from app.core.cache import close_redis
from app.core.db import SessionLocal, engine
from app.models import ImportJob
from app.services.enrichment.service import close_pipeline
from app.services.ingestion.import_service import import_csv
from app.services.jobs.enrich_job import run_import_job
from app.services.scoring.service import seed_default_profiles

DEFAULT_CSV = Path(__file__).resolve().parents[2] / "data" / "sample_leads.csv"


async def main(path: Path) -> None:
    if not path.exists():
        sys.exit(f"can't find {path}")

    async with SessionLocal() as session:
        await seed_default_profiles(session)
        result = await import_csv(session, path.read_bytes(), path.name)
        job = result.job

    print(f"imported {job.total_rows} rows, {job.duplicates_removed} duplicates removed")
    print("enriching... (crawling public sites, checking mx records, scoring)")

    started = time.perf_counter()
    await run_import_job(job.id)

    async with SessionLocal() as session:
        job = await session.get(ImportJob, job.id)
    print(
        f"done in {time.perf_counter() - started:.0f}s - "
        f"{job.processed} enriched, {job.failed} failed ({job.status})"
    )

    await close_pipeline()
    await close_redis()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV))
