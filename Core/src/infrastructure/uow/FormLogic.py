from shared_db import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

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

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.field_rules = FieldRuleRepository(session)
        self.field_dependencies = FieldDependencyRepository(session)
        self.section_dependencies = SectionDependencyRepository(session)
        # Read-only access to verify references
        self.fields = FieldRepository(session)
        self.sections = SectionRepository(session)
