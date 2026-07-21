from uuid import UUID

from shared.models import (
    Criterion,
    Grade,
    Result,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CriterionRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Criterion | None:
        stmt = select(Criterion).where(Criterion.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Criterion) -> None:
        self.session.add(entry)

    async def delete(self, entry: Criterion) -> None:
        await self.session.delete(entry)


class GradeRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Grade | None:
        stmt = select(Grade).where(Grade.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Grade) -> None:
        self.session.add(entry)

    async def delete(self, entry: Grade) -> None:
        await self.session.delete(entry)


class ResultRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Result | None:
        stmt = select(Result).where(Result.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Result) -> None:
        self.session.add(entry)

    async def delete(self, entry: Result) -> None:
        await self.session.delete(entry)
