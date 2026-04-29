from uuid import UUID
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from shared_models import (
    FieldRule,
    FieldDependency,
    SectionDependency,
)


class FieldDependencyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> FieldDependency | None:
        stmt = select(FieldDependency).where(FieldDependency.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: FieldDependency) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: FieldDependency) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class FieldRuleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> FieldRule | None:
        stmt = select(FieldRule).where(FieldRule.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: FieldRule) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: FieldRule) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class SectionDependencyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> SectionDependency | None:
        stmt = select(SectionDependency).where(SectionDependency.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: SectionDependency) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: SectionDependency) -> None:
        session = cast(Session, self.session)
        session.delete(entry)
