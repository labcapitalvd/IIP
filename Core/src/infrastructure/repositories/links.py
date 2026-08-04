from uuid import UUID

from shared.db import BaseRepository
from shared.models import MultiChoiceOptionLink, UserActorLink
from sqlalchemy import select


class MultiChoiceOptionLinkRepository(BaseRepository[MultiChoiceOptionLink]):
    async def get_by_id(self, id: UUID) -> MultiChoiceOptionLink | None:
        stmt = select(MultiChoiceOptionLink).where(MultiChoiceOptionLink.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_choice(self, choice: str) -> MultiChoiceOptionLink | None:
        stmt = select(MultiChoiceOptionLink).where(
            MultiChoiceOptionLink.choice == choice
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class UserActorLinkRepository(BaseRepository[UserActorLink]):
    async def get_by_id(self, id: UUID) -> UserActorLink | None:
        stmt = select(UserActorLink).where(UserActorLink.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> UserActorLink | None:
        stmt = (
            select(UserActorLink)
            .where(UserActorLink.user_id == user_id)
            .order_by(UserActorLink.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_actor_id(self, actor_id: UUID) -> UserActorLink | None:
        stmt = select(UserActorLink).where(UserActorLink.actor_id == actor_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
