from typing import cast
from uuid import UUID

from models import Actor, ActorSegment, UserActorLink
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

    def add(self, actor: Actor) -> None:
        session = cast(Session, self.session)
        session.add(actor)

    def delete(self, actor: Actor) -> None:
        session = cast(Session, self.session)
        session.delete(actor)


class ActorSegmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> ActorSegment | None:
        stmt = select(ActorSegment).where(ActorSegment.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, segment: ActorSegment) -> None:
        session = cast(Session, self.session)
        session.add(segment)

    def delete(self, segment: ActorSegment) -> None:
        session = cast(Session, self.session)
        session.delete(segment)


class UserActorLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, link: UserActorLink) -> None:
        session = cast(Session, self.session)
        session.add(link)

    def delete(self, link: UserActorLink) -> None:
        session = cast(Session, self.session)
        session.delete(link)
