from uuid import UUID
from typing import cast, List

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Form,
    Section,
    Question,
    Field,
    CardTemplate,
    Info,
    FieldGroup,
    FieldChoice,
)


class FormRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Form | None:
        stmt = select(Form).where(Form.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, form: Form) -> None:
        session = cast(Session, self.session)
        session.add(form)

    def delete(self, form: Form) -> None:
        session = cast(Session, self.session)
        session.delete(form)


class SectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Section | None:
        stmt = select(Section).where(Section.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, section: Section) -> None:
        session = cast(Session, self.session)
        session.add(section)

    def delete(self, section: Section) -> None:
        session = cast(Session, self.session)
        session.delete(section)


class QuestionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Question | None:
        stmt = select(Question).where(Question.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, question: Question) -> None:
        session = cast(Session, self.session)
        session.add(question)

    def delete(self, question: Question) -> None:
        session = cast(Session, self.session)
        session.delete(question)


class FieldRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Field | None:
        stmt = select(Field).where(Field.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, field: Field) -> None:
        session = cast(Session, self.session)
        session.add(field)

    def delete(self, field: Field) -> None:
        session = cast(Session, self.session)
        session.delete(field)


class CardTemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> CardTemplate | None:
        stmt = select(CardTemplate).where(CardTemplate.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, template: CardTemplate) -> None:
        session = cast(Session, self.session)
        session.add(template)

    def delete(self, template: CardTemplate) -> None:
        session = cast(Session, self.session)
        session.delete(template)


class InfoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Info | None:
        stmt = select(Info).where(Info.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, info: Info) -> None:
        session = cast(Session, self.session)
        session.add(info)

    def delete(self, info: Info) -> None:
        session = cast(Session, self.session)
        session.delete(info)


class FieldGroupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> FieldGroup | None:
        stmt = select(FieldGroup).where(FieldGroup.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, group: FieldGroup) -> None:
        session = cast(Session, self.session)
        session.add(group)

    def delete(self, group: FieldGroup) -> None:
        session = cast(Session, self.session)
        session.delete(group)


class FieldChoiceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> FieldChoice | None:
        stmt = select(FieldChoice).where(FieldChoice.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, choice: FieldChoice) -> None:
        session = cast(Session, self.session)
        session.add(choice)

    def delete(self, choice: FieldChoice) -> None:
        session = cast(Session, self.session)
        session.delete(choice)
