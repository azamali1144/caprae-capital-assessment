import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.v1.leads import FiltersDep
from app.services.export.csv_exporter import stream_csv

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/csv")
async def export_csv(
    filters: FiltersDep,
    ids: Annotated[list[uuid.UUID], Query()] = [],  # noqa: B006 - "export selected"
):
    filename = f"leadlens-{date.today().isoformat()}.csv"
    return StreamingResponse(
        stream_csv(filters, ids or None),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
