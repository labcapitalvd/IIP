from uuid import UUID

from shared.db import BaseRepository
from shared.models import (
    CardTemplate,
    Field,
    FieldChoice,
    FieldGroup,
    FieldRule,
    FileType,
    Form,
    Question,
    Section,
    SectionType,
    Submission,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload


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

    async def list_with_submission_flag(self) -> list[tuple[Form, bool]]:
        """Todos los formularios (más recientes primero) y si ya tienen respuestas."""
        has_submissions = (
            select(Submission.id).where(Submission.form_id == Form.id).exists()
        )
        stmt = select(Form, has_submissions).order_by(Form.updated_at.desc())
        result = await self.session.execute(stmt)
        return [(form, bool(flag)) for form, flag in result.all()]

    async def list_sections_tree(self, form_id: UUID) -> list[Section]:
        """
        Todas las secciones del formulario (raíces e hijas, en plano) con su
        árbol de preguntas precargado; el llamador las anida por `parent_id`.
        """
        fields = (
            selectinload(Section.questions)
            .selectinload(Question.card_template)
            .selectinload(CardTemplate.field_groups)
            .selectinload(FieldGroup.fields)
        )
        stmt = (
            select(Section)
            .where(Section.form_id == form_id)
            .options(
                selectinload(Section.type),
                selectinload(Section.questions).selectinload(Question.criteria),
                fields.selectinload(Field.field_type),
                fields.selectinload(Field.field_choices),
                fields.selectinload(Field.field_rules).selectinload(FieldRule.rule),
                fields.selectinload(Field.dependencies_triggered_by_others),
            )
            .order_by(Section.display_order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


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
