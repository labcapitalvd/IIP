from uuid import UUID

from shared.db import BaseRepository
from shared.models import (
    FieldType,
    RelationalOperator,
    RuleType,
    SubmissionStatusType,
)
from sqlalchemy import select


class FieldTypeRepository(BaseRepository[FieldType]):
    async def get_by_code(self, code: str) -> FieldType | None:
        stmt = select(FieldType).where(FieldType.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> FieldType | None:
        stmt = select(FieldType).where(FieldType.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RelationalOperatorRepository(BaseRepository[RelationalOperator]):
    async def get_by_code(self, code: str) -> RelationalOperator | None:
        stmt = select(RelationalOperator).where(RelationalOperator.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> RelationalOperator | None:
        stmt = select(RelationalOperator).where(RelationalOperator.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RuleTypeRepository(BaseRepository[RuleType]):
    async def get_by_code(self, code: str) -> RuleType | None:
        stmt = select(RuleType).where(RuleType.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> RuleType | None:
        stmt = select(RuleType).where(RuleType.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SubmissionStatusTypeRepository(BaseRepository[SubmissionStatusType]):
    async def get_by_id(self, id: UUID) -> SubmissionStatusType | None:
        stmt = select(SubmissionStatusType).where(SubmissionStatusType.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
