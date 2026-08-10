from typing import Sequence
from uuid import UUID

from shared.models import Actor, ActorSegment, UserActorLink
from shared.db import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload


class ActorRepository(BaseRepository[Actor]):
    async def get_by_id(self, id: UUID) -> Actor | None:
        stmt = (
            select(Actor).options(joinedload(Actor.actor_segment)).where(Actor.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Actor | None:
        stmt = (
            select(Actor)
            .options(joinedload(Actor.actor_segment))
            .where(Actor.code == code)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[Actor]:
        stmt = (
            select(Actor).options(joinedload(Actor.actor_segment)).order_by(Actor.code)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ActorSegmentRepository(BaseRepository[ActorSegment]):
    async def get_by_id(self, id: UUID) -> ActorSegment | None:
        stmt = (
            select(ActorSegment)
            .options(selectinload(ActorSegment.actors))
            .where(ActorSegment.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> ActorSegment | None:
        stmt = (
            select(ActorSegment)
            .options(selectinload(ActorSegment.actors))
            .where(ActorSegment.code == code)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[ActorSegment]:
        stmt = (
            select(ActorSegment)
            .options(joinedload(ActorSegment.actors))
            .order_by(ActorSegment.code)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()


class UserActorLinkRepository(BaseRepository[UserActorLink]):
    """Inherits add, delete, and session init directly from BaseRepository."""

    pass
