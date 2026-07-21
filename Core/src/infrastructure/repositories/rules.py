from uuid import UUID

from shared.db import BaseRepository
from shared.models import (
    FieldDependency,
    FieldRule,
    SectionDependency,
)
from sqlalchemy import select


class FieldDependencyRepository(BaseRepository[FieldDependency]):
    async def get_by_id(self, id: UUID) -> FieldDependency | None:
        stmt = select(FieldDependency).where(FieldDependency.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class FieldRuleRepository(BaseRepository[FieldRule]):
    async def get_by_id(self, id: UUID) -> FieldRule | None:
        stmt = select(FieldRule).where(FieldRule.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SectionDependencyRepository(BaseRepository[SectionDependency]):
    async def get_by_id(self, id: UUID) -> SectionDependency | None:
        stmt = select(SectionDependency).where(SectionDependency.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
