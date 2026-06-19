from typing import Sequence
from uuid import UUID

from shared.models import Actor, ActorSegment, UserActorLink
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload


class ActorRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Actor | None:
        stmt = (
            select(Actor).options(joinedload(Actor.actor_segment)).where(Actor.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_label(self, label: str) -> Actor | None:
        stmt = (
            select(Actor)
            .options(joinedload(Actor.actor_segment))
            .where(Actor.label == label)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[Actor]:
        stmt = (
            select(Actor).options(joinedload(Actor.actor_segment)).order_by(Actor.label)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def add(self, entry: Actor) -> None:
        self.session.add(entry)

    def delete(self, entry: Actor) -> None:
        self.session.delete(entry)


class ActorSegmentRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> ActorSegment | None:
        stmt = (
            select(ActorSegment)
            .options(selectinload(ActorSegment.actors))
            .where(ActorSegment.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_label(self, label: str) -> ActorSegment | None:
        stmt = (
            select(ActorSegment)
            .options(selectinload(ActorSegment.actors))
            .where(ActorSegment.label == label)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[ActorSegment]:
        stmt = (
            select(ActorSegment).options(joinedload(ActorSegment.actors)).order_by(ActorSegment.label)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    def add(self, entry: ActorSegment) -> None:
        self.session.add(entry)

    def delete(self, entry: ActorSegment) -> None:
        self.session.delete(entry)


class UserActorLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    def add(self, entry: UserActorLink) -> None:
        self.session.add(entry)

    def delete(self, entry: UserActorLink) -> None:
        self.session.delete(entry)
