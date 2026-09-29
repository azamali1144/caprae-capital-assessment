from fastapi import APIRouter

from app.api.v1 import health, icp_profiles, imports

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(imports.router)
api_router.include_router(icp_profiles.router)
