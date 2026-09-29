import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IcpProfile


class IcpRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> list[IcpProfile]:
        rows = await self.session.scalars(
            select(IcpProfile).order_by(IcpProfile.is_active.desc(), IcpProfile.created_at)
        )
        return list(rows)

    async def get(self, profile_id: uuid.UUID) -> IcpProfile | None:
        return await self.session.get(IcpProfile, profile_id)

    async def active(self) -> IcpProfile | None:
        return await self.session.scalar(select(IcpProfile).where(IcpProfile.is_active).limit(1))

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(IcpProfile))

    async def create(self, **fields) -> IcpProfile:
        profile = IcpProfile(**fields)
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def set_active(self, profile: IcpProfile) -> None:
        # only one active profile at a time
        await self.session.execute(update(IcpProfile).values(is_active=False))
        profile.is_active = True
        await self.session.flush()
