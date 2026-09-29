import uuid

from fastapi import APIRouter, status

from app.api.deps import SessionDep
from app.core.errors import NotFound
from app.repositories.icp_repo import IcpRepo
from app.schemas.icp_profile import ActivateOut, IcpProfileIn, IcpProfileOut
from app.services.scoring.service import rescore_all

router = APIRouter(prefix="/icp-profiles", tags=["icp profiles"])


@router.get("", response_model=list[IcpProfileOut])
async def list_profiles(session: SessionDep):
    return await IcpRepo(session).list()


@router.post("", response_model=IcpProfileOut, status_code=status.HTTP_201_CREATED)
async def create_profile(body: IcpProfileIn, session: SessionDep):
    profile = await IcpRepo(session).create(
        name=body.name, mode=body.mode, rules=body.rules.model_dump(exclude_none=True)
    )
    await session.commit()
    await session.refresh(profile)
    return profile


@router.put("/{profile_id}", response_model=IcpProfileOut)
async def update_profile(profile_id: uuid.UUID, body: IcpProfileIn, session: SessionDep):
    repo = IcpRepo(session)
    profile = await repo.get(profile_id)
    if not profile:
        raise NotFound("ICP profile")
    profile.name = body.name
    profile.mode = body.mode
    profile.rules = body.rules.model_dump(exclude_none=True)
    await session.commit()
    await session.refresh(profile)
    # editing the active one changes scores, so keep them in sync
    if profile.is_active:
        await rescore_all(session, profile)
    return profile


@router.post("/{profile_id}/activate", response_model=ActivateOut)
async def activate_profile(profile_id: uuid.UUID, session: SessionDep):
    repo = IcpRepo(session)
    profile = await repo.get(profile_id)
    if not profile:
        raise NotFound("ICP profile")
    await repo.set_active(profile)
    await session.commit()
    rescored = await rescore_all(session, profile)
    await session.refresh(profile)
    return ActivateOut(profile=IcpProfileOut.model_validate(profile), rescored=rescored)
