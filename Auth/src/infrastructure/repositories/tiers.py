from shared.db import BaseRepository
from shared.models import UserTier
from sqlalchemy import select


class TierRepository(BaseRepository[UserTier]):
    async def get_by_code(self, label: str) -> UserTier | None:
        stmt = select(UserTier).where(UserTier.label == label)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default(self) -> UserTier:
        tier = await self.get_by_code("STANDARD")
        if not tier:
            raise ValueError("Default tier not found")
        return tier
