from typing import cast
from uuid import UUID

from models import (
    Answer,
    AnswerBoolean,
    AnswerCardEntry,
    AnswerDate,
    AnswerFile,
    AnswerMultiChoice,
    AnswerNumeric,
    AnswerSingleChoice,
    AnswerText,
    Submission,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class AnswerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Answer | None:
        stmt = select(Answer).where(Answer.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Answer) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: Answer) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class AnswerBooleanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnswerBoolean | None:
        stmt = select(AnswerBoolean).where(AnswerBoolean.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: AnswerBoolean) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: AnswerBoolean) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class AnswerCardEntryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnswerCardEntry | None:
        stmt = select(AnswerCardEntry).where(AnswerCardEntry.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: AnswerCardEntry) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: AnswerCardEntry) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class AnswerDateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnswerDate | None:
        stmt = select(AnswerDate).where(AnswerDate.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: AnswerDate) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: AnswerDate) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class AnswerFileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnswerFile | None:
        stmt = select(AnswerFile).where(AnswerFile.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: AnswerFile) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: AnswerFile) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class AnswerMultiChoiceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnswerMultiChoice | None:
        stmt = select(AnswerMultiChoice).where(AnswerMultiChoice.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: AnswerMultiChoice) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: AnswerMultiChoice) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class AnswerNumericRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnswerNumeric | None:
        stmt = select(AnswerNumeric).where(AnswerNumeric.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: AnswerNumeric) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: AnswerNumeric) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class AnswerSingleChoiceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnswerSingleChoice | None:
        stmt = select(AnswerSingleChoice).where(AnswerSingleChoice.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: AnswerSingleChoice) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: AnswerSingleChoice) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class AnswerTextRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnswerText | None:
        stmt = select(AnswerText).where(AnswerText.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: AnswerText) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: AnswerText) -> None:
        session = cast(Session, self.session)
        session.delete(entry)


class SubmissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Submission | None:
        stmt = select(Submission).where(Submission.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Submission) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete(self, entry: Submission) -> None:
        session = cast(Session, self.session)
        session.delete(entry)
