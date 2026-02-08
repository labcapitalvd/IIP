from uuid import UUID
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Submission,
    Answer,
    CardEntry,
    UserSubmissionLink,
)


class SubmissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Submission | None:
        stmt = select(Submission).where(Submission.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, submission: Submission) -> None:
        session = cast(Session, self.session)
        session.add(submission)

    def delete(self, submission: Submission) -> None:
        session = cast(Session, self.session)
        session.delete(submission)


class AnswerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Answer | None:
        stmt = select(Answer).where(Answer.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, answer: Answer) -> None:
        session = cast(Session, self.session)
        session.add(answer)

    def delete(self, answer: Answer) -> None:
        session = cast(Session, self.session)
        session.delete(answer)


class CardEntryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> CardEntry | None:
        stmt = select(CardEntry).where(CardEntry.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: CardEntry) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: CardEntry) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class UserSubmissionLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, link: UserSubmissionLink) -> None:
        session = cast(Session, self.session)
        session.add(link)

    def delete(self, link: UserSubmissionLink) -> None:
        session = cast(Session, self.session)
        session.delete(link)
