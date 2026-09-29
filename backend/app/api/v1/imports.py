import uuid

from fastapi import APIRouter, UploadFile, status

from app.api.deps import SessionDep
from app.core.errors import AppError, NotFound
from app.repositories.import_repo import ImportRepo
from app.schemas.import_job import DomainsImportIn, ImportCreatedOut, ImportJobOut
from app.services.ingestion import import_service
from app.services.ingestion.csv_parser import MAX_BYTES, CsvImportError

router = APIRouter(prefix="/imports", tags=["imports"])


def _created(result: import_service.ImportResult) -> ImportCreatedOut:
    return ImportCreatedOut(
        job_id=result.job.id,
        job=ImportJobOut.model_validate(result.job),
        unmapped_columns=result.unmapped,
        warnings=result.warnings,
    )


@router.post("/csv", response_model=ImportCreatedOut, status_code=status.HTTP_201_CREATED)
async def upload_csv(file: UploadFile, session: SessionDep):
    name = (file.filename or "").lower()
    if name and not name.endswith((".csv", ".txt")):
        raise AppError("IMPORT_INVALID_CSV", "Please upload a .csv file.")

    data = await file.read(MAX_BYTES + 1)
    try:
        result = await import_service.import_csv(session, data, file.filename)
    except CsvImportError as exc:
        raise AppError(exc.code, exc.message) from exc
    return _created(result)


@router.post("/domains", response_model=ImportCreatedOut, status_code=status.HTTP_201_CREATED)
async def import_domains(body: DomainsImportIn, session: SessionDep):
    try:
        result = await import_service.import_domains(session, body.domains)
    except CsvImportError as exc:
        raise AppError(exc.code, exc.message) from exc
    return _created(result)


@router.get("", response_model=list[ImportJobOut])
async def list_imports(session: SessionDep, limit: int = 20):
    return await ImportRepo(session).recent(min(limit, 100))


@router.get("/{job_id}", response_model=ImportJobOut)
async def get_import(job_id: uuid.UUID, session: SessionDep):
    job = await ImportRepo(session).get(job_id)
    if not job:
        raise NotFound("Import job")
    return job
