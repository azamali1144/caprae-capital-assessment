import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DomainsImportIn(BaseModel):
    domains: list[str] = Field(min_length=1, max_length=5000)


class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    filename: str | None
    status: str
    total_rows: int
    duplicates_removed: int
    processed: int
    failed: int
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class ImportCreatedOut(BaseModel):
    job_id: uuid.UUID
    job: ImportJobOut
    unmapped_columns: list[str] = []
    warnings: list[str] = []
