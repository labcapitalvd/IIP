from typing import cast
from uuid import UUID

from models import MultiChoiceOptionLink, UserActorLink, UserSubmissionLink
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class MultiChoiceOptionLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

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

    def add(self, entry: MultiChoiceOptionLink) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: MultiChoiceOptionLink) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class UserActorLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> UserActorLink | None:
        stmt = select(UserActorLink).where(UserActorLink.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: UserActorLink) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: UserActorLink) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class UserSubmissionLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> UserSubmissionLink | None:
        stmt = select(UserSubmissionLink).where(UserSubmissionLink.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: UserSubmissionLink) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: UserSubmissionLink) -> None:
        session = cast(Session, self.session)
        session.delete(entry)
