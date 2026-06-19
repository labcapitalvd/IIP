from shared.db import UnitOfWork
from ..repositories import (
    FieldDependencyRepository,
    FieldRepository,
    FieldRuleRepository,
    SectionDependencyRepository,
    SectionRepository,
)


class FormLogicUoW(UnitOfWork):
    """
    Unit of Work for Form Logic Context.
    Handles skip logic, dependencies, and validation rules.
    """

    field_rules: FieldRuleRepository
    field_dependencies: FieldDependencyRepository
    section_dependencies: SectionDependencyRepository
    fields: FieldRepository
    sections: SectionRepository

    async def __aenter__(self):
        await super().__aenter__()
        assert self.session is not None

        self.field_rules = FieldRuleRepository(self.session)
        self.field_dependencies = FieldDependencyRepository(self.session)
        self.section_dependencies = SectionDependencyRepository(self.session)
        # Read-only access to verify references
        self.fields = FieldRepository(self.session)
        self.sections = SectionRepository(self.session)
        return self
