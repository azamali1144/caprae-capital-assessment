import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportJob


class ImportRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, source: str, filename: str | None = None, **fields) -> ImportJob:
        job = ImportJob(source=source, filename=filename, **fields)
        self.session.add(job)
        await self.session.flush()
        return job

    async def get(self, job_id: uuid.UUID) -> ImportJob | None:
        return await self.session.get(ImportJob, job_id)

    async def recent(self, limit: int = 20) -> list[ImportJob]:
        rows = await self.session.scalars(
            select(ImportJob).order_by(ImportJob.created_at.desc()).limit(limit)
        )
        return list(rows)
