from typing import cast
from uuid import UUID

from shared.models import (
    Answer,
    Submission, AnswerCardEntry, SubmissionStatusType,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload


class AnswerRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Answer | None:
        stmt = select(Answer).where(Answer.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Answer) -> None:
        self.session.add(entry)

    async def delete(self, entry: Answer) -> None:
        await self.session.delete(entry)


class SubmissionRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Submission | None:
        stmt = (
            select(Submission)
            .where(Submission.id == id)
            .options(
                selectinload(Submission.answers)
                .selectinload(Answer.card_entry)
                .selectinload(AnswerCardEntry.answers)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_status_by_label(self, label:str) -> SubmissionStatusType | None:
        print(f"DEBUG: Looking for label: '{label}'")
        stmt = (
            select(SubmissionStatusType)
            .where(SubmissionStatusType.label == label)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Submission) -> None:
        self.session.add(entry)

    async def delete(self, entry: Submission) -> None:
        await self.session.delete(entry)
