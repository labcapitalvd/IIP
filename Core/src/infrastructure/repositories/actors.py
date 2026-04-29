from typing import cast
from uuid import UUID

from shared_models import Actor, ActorSegment, UserActorLink
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class ActorRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Actor | None:
        stmt = select(Actor).where(Actor.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Actor | None:
        stmt = select(Actor).where(Actor.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Actor) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: Actor) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class ActorSegmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> ActorSegment | None:
        stmt = select(ActorSegment).where(ActorSegment.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: ActorSegment) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: ActorSegment) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class UserActorLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, entry: UserActorLink) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: UserActorLink) -> None:
        session = cast(Session, self.session)
        session.delete(entry)
