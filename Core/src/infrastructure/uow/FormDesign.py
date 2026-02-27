from shared_db import UnitOfWork
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

    forms: FormRepository
    sections: SectionRepository
    questions: QuestionRepository
    fields: FieldRepository
    field_groups: FieldGroupRepository
    field_choices: FieldChoiceRepository
    infos: InfoRepository
    card_templates: CardTemplateRepository

    async def __aenter__(self):
        await super().__aenter__()
        assert self.session is not None

        self.forms = FormRepository(self.session)
        self.sections = SectionRepository(self.session)
        self.questions = QuestionRepository(self.session)
        self.fields = FieldRepository(self.session)
        self.field_groups = FieldGroupRepository(self.session)
        self.field_choices = FieldChoiceRepository(self.session)
        self.infos = InfoRepository(self.session)
        self.card_templates = CardTemplateRepository(self.session)
        return self
