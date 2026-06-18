from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from shared_db import (
    Base,
    column_fk,
    column_jsonb,
    column_short_text,
    column_updated_at,
)
from sqlalchemy.orm import Mapped, relationship

from .targets import TargetTable

if TYPE_CHECKING:
    from .forms import Field, Section
    from .reference import RelationalOperator, RuleType


class FieldDependency(Base):
    """Represents a conditional visibility dependency between two fields."""

    __tablename__ = TargetTable.FIELD_DEPENDENCIES.table
    __table_args__ = {"schema": TargetTable.FIELD_DEPENDENCIES.schema}

    target_field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id", ondelete="CASCADE"
    )
    depends_on_field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id", ondelete="CASCADE"
    )
    relational_operator_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.RELATIONAL_OPERATORS.fq_name}.id", ondelete="SET NULL"
    )

    expected_value: Mapped[dict] = column_jsonb()

    operator_type: Mapped["RelationalOperator"] = relationship(
        "RelationalOperator", back_populates="field_dependencies"
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


class FieldRule(Base):
    """Assigns real-time input mutation or validation rules to execution elements."""

    __tablename__ = TargetTable.FIELD_RULES.table
    __table_args__ = {"schema": TargetTable.FIELD_RULES.schema}

    field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id", ondelete="CASCADE"
    )
    rule_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.RULE_TYPES.fq_name}.id", ondelete="CASCADE"
    )

    rule_value: Mapped[str] = column_short_text(255)
    error_message: Mapped[str] = column_short_text(255)
    updated_at: Mapped[datetime] = column_updated_at()

    rule: Mapped["RuleType"] = relationship("RuleType", back_populates="field_rules")
    field: Mapped["Field"] = relationship("Field", back_populates="field_rules")


class SectionDependency(Base):
    """Represents a conditional visibility dependency tracking entire layout layers."""

    __tablename__ = TargetTable.SECTION_DEPENDENCIES.table
    __table_args__ = {"schema": TargetTable.SECTION_DEPENDENCIES.schema}

    target_section_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id", ondelete="CASCADE"
    )
    depends_on_section_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id", ondelete="CASCADE"
    )
    relational_operator_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.RELATIONAL_OPERATORS.fq_name}.id", ondelete="SET NULL"
    )

    expected_value: Mapped[dict] = column_jsonb()

    operator_type: Mapped["RelationalOperator"] = relationship(
        "RelationalOperator", back_populates="section_dependencies"
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
