from shared_db import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import (
    CardTemplateRepository,
    FieldChoiceRepository,
    FieldGroupRepository,
    FieldRepository,
    FormRepository,
    InfoRepository,
    QuestionRepository,
    SectionRepository,
)


class FormDesignUoW(UnitOfWork):
    """
    Unit of Work for Form Design Context.
    Handles creation and modification of form structure (Sections, Fields, Choices).
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.forms = FormRepository(session)
        self.sections = SectionRepository(session)
        self.questions = QuestionRepository(session)
        self.fields = FieldRepository(session)
        self.field_groups = FieldGroupRepository(session)
        self.field_choices = FieldChoiceRepository(session)
        self.infos = InfoRepository(session)
        self.card_templates = CardTemplateRepository(session)
