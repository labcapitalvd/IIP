from typing import cast
from uuid import UUID

from shared_models import (
    CardTemplate,
    Field,
    FieldChoice,
    FieldGroup,
    Form,
    Question,
    Section,
    SectionType,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class CardTemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> CardTemplate | None:
        stmt = select(CardTemplate).where(CardTemplate.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: CardTemplate) -> None:
        self.session.add(entry)

    def delete(self, entry: CardTemplate) -> None:
        self.session.delete(entry)


class FieldChoiceRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> FieldChoice | None:
        stmt = select(FieldChoice).where(FieldChoice.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: FieldChoice) -> None:
        self.session.add(entry)

    def delete(self, entry: FieldChoice) -> None:
        self.session.delete(entry)


class FieldGroupRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> FieldGroup | None:
        stmt = select(FieldGroup).where(FieldGroup.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: FieldGroup) -> None:
        self.session.add(entry)

    def delete(self, entry: FieldGroup) -> None:
        self.session.delete(entry)


class FieldRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Field | None:
        stmt = select(Field).where(Field.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Field) -> None:
        self.session.add(entry)

    def delete(self, entry: Field) -> None:
        self.session.delete(entry)


class FormRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Form | None:
        stmt = select(Form).where(Form.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_anno(self, anno: int) -> Form | None:
        """Obtiene un formulario por su año (que es único)."""
        stmt = select(Form).where(Form.anno == anno)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Form) -> None:
        self.session.add(entry)

    def delete(self, entry: Form) -> None:
        self.session.delete(entry)


class QuestionRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Question | None:
        stmt = select(Question).where(Question.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Question) -> None:
        self.session.add(entry)

    def delete(self, entry: Question) -> None:
        self.session.delete(entry)


class SectionRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Section | None:
        stmt = select(Section).where(Section.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: Section) -> None:
        self.session.add(entry)

    def delete(self, entry: Section) -> None:
        self.session.delete(entry)


class SectionTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> SectionType | None:
        stmt = select(SectionType).where(SectionType.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, entry: SectionType) -> None:
        self.session.add(entry)

    def delete(self, entry: SectionType) -> None:
        self.session.delete(entry)
