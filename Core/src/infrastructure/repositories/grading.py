from uuid import UUID

from shared.db import BaseRepository
from shared.models import (
    Criterion,
    Grade,
    Result,
)
from sqlalchemy import select


class CriterionRepository(BaseRepository[Criterion]):
    async def get_by_id(self, id: UUID) -> Criterion | None:
        stmt = select(Criterion).where(Criterion.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class GradeRepository(BaseRepository[Grade]):
    async def get_by_id(self, id: UUID) -> Grade | None:
        stmt = select(Grade).where(Grade.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ResultRepository(BaseRepository[Result]):
    async def get_by_id(self, id: UUID) -> Result | None:
        stmt = select(Result).where(Result.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
