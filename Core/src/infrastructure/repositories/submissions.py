from typing import cast
from uuid import UUID

from models import (
    Answer,
    Submission,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class AnswerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Answer | None:
        stmt = select(Answer).where(Answer.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Answer) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: Answer) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class SubmissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Submission | None:
        stmt = select(Submission).where(Submission.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Submission) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: Submission) -> None:
        session = cast(Session, self.session)
        session.delete(entry)
