from uuid import UUID

from shared.db import BaseRepository
from shared.models import (
    Answer,
    AnswerCardEntry,
    Submission,
    SubmissionStatusType,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class AnswerRepository(BaseRepository[Answer]):
    async def get_by_id(self, id: UUID) -> Answer | None:
        stmt = select(Answer).where(Answer.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SubmissionRepository(BaseRepository[Submission]):
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

    async def get_status_by_label(self, label: str) -> SubmissionStatusType | None:
        print(f"DEBUG: Looking for label: '{label}'")
        stmt = select(SubmissionStatusType).where(SubmissionStatusType.label == label)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
