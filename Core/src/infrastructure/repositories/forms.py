from uuid import UUID

from shared.db import BaseRepository
from shared.models import (
    CardTemplate,
    Field,
    FieldChoice,
    FieldGroup,
    FileType,
    Form,
    Question,
    Section,
    SectionType,
)
from sqlalchemy import select


class CardTemplateRepository(BaseRepository[CardTemplate]):
    model = CardTemplate 


class FieldChoiceRepository(BaseRepository[FieldChoice]):
    model = FieldChoice


class FieldGroupRepository(BaseRepository[FieldGroup]):
    model = FieldGroup 


class FieldRepository(BaseRepository[Field]):
    model = Field 


class FileTypeRepository(BaseRepository[FileType]):
    model = FileType

    async def list_all(self) -> list[FileType]:
        result = await self.session.execute(select(FileType).order_by(FileType.category, FileType.label))
        return list(result.scalars().all())

    async def get_by_codes(self, codes: list[str]) -> list[FileType]:
        result = await self.session.execute(select(FileType).where(FileType.code.in_(codes)))
        return list(result.scalars().all())


class FormRepository(BaseRepository[Form]):
    model = Form 
    async def get_by_code(self, code: str) -> Form | None:
        """Obtiene un formulario por su código (que es único)."""
        stmt = select(Form).where(Form.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class QuestionRepository(BaseRepository[Question]):
    model = Question 


class SectionRepository(BaseRepository[Section]):
    model = Section 


class SectionTypeRepository(BaseRepository[SectionType]):
    model = SectionType

    async def get_by_code(self, code: str) -> SectionType | None:
        stmt = select(SectionType).where(SectionType.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
