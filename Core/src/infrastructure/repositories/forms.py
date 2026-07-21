from uuid import UUID

from shared.db import BaseRepository
from shared.models import (
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


class CardTemplateRepository(BaseRepository[CardTemplate]):
    async def get_by_id(self, id: UUID) -> CardTemplate | None:
        stmt = select(CardTemplate).where(CardTemplate.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class FieldChoiceRepository(BaseRepository[FieldChoice]):
    async def get_by_id(self, id: UUID) -> FieldChoice | None:
        stmt = select(FieldChoice).where(FieldChoice.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class FieldGroupRepository(BaseRepository[FieldGroup]):
    async def get_by_id(self, id: UUID) -> FieldGroup | None:
        stmt = select(FieldGroup).where(FieldGroup.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class FieldRepository(BaseRepository[Field]):
    async def get_by_id(self, id: UUID) -> Field | None:
        stmt = select(Field).where(Field.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class FormRepository(BaseRepository[Form]):
    async def get_by_id(self, id: UUID) -> Form | None:
        stmt = select(Form).where(Form.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_anno(self, anno: int) -> Form | None:
        """Obtiene un formulario por su año (que es único)."""
        stmt = select(Form).where(Form.anno == anno)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class QuestionRepository(BaseRepository[Question]):
    async def get_by_id(self, id: UUID) -> Question | None:
        stmt = select(Question).where(Question.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SectionRepository(BaseRepository[Section]):
    async def get_by_id(self, id: UUID) -> Section | None:
        stmt = select(Section).where(Section.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SectionTypeRepository(BaseRepository[SectionType]):
    async def get_by_id(self, id: UUID) -> SectionType | None:
        stmt = select(SectionType).where(SectionType.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
