from typing import cast
from uuid import UUID

from models import (
    FieldType,
    RelationalOperator,
    RuleType,
    SubmissionStatusType,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class FieldTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> FieldType | None:
        stmt = select(FieldType).where(FieldType.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: FieldType) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: FieldType) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class RelationalOperatorRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> RelationalOperator | None:
        stmt = select(RelationalOperator).where(RelationalOperator.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: RelationalOperator) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: RelationalOperator) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class RuleTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> RuleType | None:
        stmt = select(RuleType).where(RuleType.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: RuleType) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: RuleType) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class SubmissionStatusTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> SubmissionStatusType | None:
        stmt = select(SubmissionStatusType).where(SubmissionStatusType.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: SubmissionStatusType) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: SubmissionStatusType) -> None:
        session = cast(Session, self.session)
        session.delete(entry)
