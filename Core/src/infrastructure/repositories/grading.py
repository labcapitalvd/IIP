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

    def add(self, entry: Criteria) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: Criteria) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class GradeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Grade | None:
        stmt = select(Grade).where(Grade.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Grade) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: Grade) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class ResultRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Result | None:
        stmt = select(Result).where(Result.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Result) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: Result) -> None:
        session = cast(Session, self.session)
        session.delete(entry)
