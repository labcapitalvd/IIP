from typing import cast
from uuid import UUID

from models import (
    Criteria,
    Grade,
    Result,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class CriteriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Criteria | None:
        stmt = select(Criteria).where(Criteria.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, criteria: Criteria) -> None:
        session = cast(Session, self.session)
        session.add(criteria)

    def delete(self, criteria: Criteria) -> None:
        session = cast(Session, self.session)
        session.delete(criteria)


class GradeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Grade | None:
        stmt = select(Grade).where(Grade.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, grade: Grade) -> None:
        session = cast(Session, self.session)
        session.add(grade)

    def delete(self, grade: Grade) -> None:
        session = cast(Session, self.session)
        session.delete(grade)


class ResultRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Result | None:
        stmt = select(Result).where(Result.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, result: Result) -> None:
        session = cast(Session, self.session)
        session.add(result)

    def delete(self, result: Result) -> None:
        session = cast(Session, self.session)
        session.delete(result)
