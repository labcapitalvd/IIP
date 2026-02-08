from uuid import UUID
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    FieldRule,
    FieldDependency,
    SectionDependency,
)


class FieldRuleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> FieldRule | None:
        stmt = select(FieldRule).where(FieldRule.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, rule: FieldRule) -> None:
        session = cast(Session, self.session)
        session.add(rule)

    def delete(self, rule: FieldRule) -> None:
        session = cast(Session, self.session)
        session.delete(rule)


class FieldDependencyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> FieldDependency | None:
        stmt = select(FieldDependency).where(FieldDependency.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, dependency: FieldDependency) -> None:
        session = cast(Session, self.session)
        session.add(dependency)

    def delete(self, dependency: FieldDependency) -> None:
        session = cast(Session, self.session)
        session.delete(dependency)


class SectionDependencyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> SectionDependency | None:
        stmt = select(SectionDependency).where(SectionDependency.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, dependency: SectionDependency) -> None:
        session = cast(Session, self.session)
        session.add(dependency)

    def delete(self, dependency: SectionDependency) -> None:
        session = cast(Session, self.session)
        session.delete(dependency)
