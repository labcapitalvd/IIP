from uuid import UUID

from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_jsonb, column_fk

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class SectionDependency(Base):
    __tablename__ = TargetTable.SECTION_DEPENDENCIES.table
    __table_args__ = {"schema": TargetTable.SECTION_DEPENDENCIES.schema}

    target_section_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id",
        ondelete="CASCADE"
    )# The section whose visibility or state depends on another section.

    depends_on_section_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id",
        ondelete="CASCADE"
    )# The section that triggers the dependency.
    
    relational_operator_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.RELATIONAL_OPERATORS.fq_name}.id", ondelete="SET NULL"
    )# "Defines how the expected_value is compared (e.g. EQUALS, GREATER_THAN)."

    expected_value: Mapped[dict] = column_jsonb() # # The value (or structure) that must match for the dependency to be satisfied.
    
    
    operator_type: Mapped["RelationalOperator"] = relationship(
        "RelationalOperator", back_populates="section_dependency", uselist=False
    )
    target_section: Mapped["Section"] = relationship(
        "Section",
        foreign_keys=[target_section_id],
        back_populates="dependencies_triggered_by_others",
    )
    
    depends_on_section: Mapped["Section"] = relationship(
        "Section",
        foreign_keys=[depends_on_section_id],
        back_populates="dependencies_it_triggers",
    )
