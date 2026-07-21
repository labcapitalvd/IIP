from uuid import UUID

from shared.models import (
    FieldDependency,
    FieldRule,
    SectionDependency,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FieldDependencyRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> FieldDependency | None:
        stmt = select(FieldDependency).where(FieldDependency.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: FieldDependency) -> None:
        self.session.add(entry)

    async def delete(self, entry: FieldDependency) -> None:
        await self.session.delete(entry)


class FieldRuleRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> FieldRule | None:
        stmt = select(FieldRule).where(FieldRule.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: FieldRule) -> None:
        self.session.add(entry)

    async def delete(self, entry: FieldRule) -> None:
        await self.session.delete(entry)


class SectionDependencyRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> SectionDependency | None:
        stmt = select(SectionDependency).where(SectionDependency.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: SectionDependency) -> None:
        self.session.add(entry)

    async def delete(self, entry: SectionDependency) -> None:
        await self.session.delete(entry)
