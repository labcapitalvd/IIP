from shared.db import UnitOfWork
from ..repositories import (
    CardTemplateRepository,
    FieldChoiceRepository,
    FieldGroupRepository,
    FieldRepository,
    FieldTypeRepository,
    FormRepository,
    QuestionRepository,
    SectionRepository,
    SectionTypeRepository,
)


class FormDesignUoW(UnitOfWork):
    """
    Unit of Work for Form Design Context.
    Handles creation and modification of form structure (Sections, Fields, Choices).
    """

    forms: FormRepository
    sections: SectionRepository
    section_types: SectionTypeRepository
    questions: QuestionRepository
    fields: FieldRepository
    field_types: FieldTypeRepository
    field_groups: FieldGroupRepository
    field_choices: FieldChoiceRepository
    card_templates: CardTemplateRepository

    def _init_repositories(self) -> None:
        assert self.session is not None

        self.forms = FormRepository(self.session)
        self.sections = SectionRepository(self.session)
        self.section_types = SectionTypeRepository(self.session)
        self.questions = QuestionRepository(self.session)
        self.fields = FieldRepository(self.session)
        self.field_types = FieldTypeRepository(self.session)
        self.field_groups = FieldGroupRepository(self.session)
        self.field_choices = FieldChoiceRepository(self.session)
        self.card_templates = CardTemplateRepository(self.session)
