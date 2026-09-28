from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.api.deps import SessionDep
from app.core.cache import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(response: Response, session: SessionDep):
    checks = {"db": "ok", "redis": "ok"}

    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        checks["db"] = "down"

    try:
        await get_redis().ping()
    except Exception:
        checks["redis"] = "down"

    healthy = all(v == "ok" for v in checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if healthy else "degraded", **checks}
