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
    model = CardTemplate 


class FieldChoiceRepository(BaseRepository[FieldChoice]):
    model = FieldChoice


class FieldGroupRepository(BaseRepository[FieldGroup]):
    model = FieldGroup 


class FieldRepository(BaseRepository[Field]):
    model = Field 


class FormRepository(BaseRepository[Form]):
    model = Form 
    async def get_by_code(self, code: int) -> Form | None:
        """Obtiene un formulario por su año (que es único)."""
        stmt = select(Form).where(Form.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class QuestionRepository(BaseRepository[Question]):
    model = Question 


class SectionRepository(BaseRepository[Section]):
    model = Section 


class SectionTypeRepository(BaseRepository[SectionType]):
    model = SectionType
