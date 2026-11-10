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
                .selectinload(AnswerCardEntry.child_answers)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_status_by_code(self, code: str) -> SubmissionStatusType | None:
        stmt = select(SubmissionStatusType).where(SubmissionStatusType.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_actor_form(
        self, actor_id: UUID, form_id: UUID
    ) -> list[tuple[Submission, str]]:
        """Existing submissions of this entity for this form, with their status code."""
        stmt = (
            select(Submission, SubmissionStatusType.code)
            .join(SubmissionStatusType, SubmissionStatusType.id == Submission.status_id)
            .where(Submission.actor_id == actor_id, Submission.form_id == form_id)
        )
        return [(sub, code) for sub, code in (await self.session.execute(stmt)).all()]
