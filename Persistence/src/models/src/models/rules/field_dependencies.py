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


class FieldDependency(Base):
    """Represents a dependency between two fields (e.g., show Field B if Field A = X)."""
    __tablename__ = TargetTable.FIELD_DEPENDENCIES.table
    __table_args__ = {"schema": TargetTable.FIELD_DEPENDENCIES.schema}

    target_field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id",
        ondelete="CASCADE"
    )# The field whose visibility or state depends on another field.

    depends_on_field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id",
        ondelete="CASCADE"
    )# The field that triggers the dependency.
    
    relational_operator_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.RELATIONAL_OPERATORS.fq_name}.id", ondelete="SET NULL"
    )# "Defines how the expected_value is compared (e.g. EQUALS, GREATER_THAN)."

    expected_value: Mapped[dict] = column_jsonb() # # The value (or structure) that must match for the dependency to be satisfied.
    
    
    operator_type: Mapped["RelationalOperator"] = relationship(
        "RelationalOperator", back_populates="field_dependency", uselist=False
    )
    target_field: Mapped["Field"] = relationship(
        "Field",
        foreign_keys=[target_field_id],
        back_populates="dependencies_triggered_by_others",
    )
    depends_on_field: Mapped["Field"] = relationship(
        "Field",
        foreign_keys=[depends_on_field_id],
        back_populates="dependencies_it_triggers",
    )
