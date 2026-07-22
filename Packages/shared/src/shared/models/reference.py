from typing import TYPE_CHECKING, List

from shared.db import (
    Base,
    column_long_text,
    column_short_text,
)
from sqlalchemy.orm import Mapped, relationship

from .targets import TargetTable

if TYPE_CHECKING:
    from .forms import Field
    from .rules import FieldDependency, FieldRule, SectionDependency
    from .submissions import Submission


class FieldType(Base):
    __tablename__ = TargetTable.FIELD_TYPES.table
    __table_args__ = {"schema": TargetTable.FIELD_TYPES.schema}

    code: Mapped[str] = column_short_text(length=50, unique=True)
    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    fields: Mapped[List["Field"]] = relationship("Field", back_populates="field_type")


class RelationalOperator(Base):
    __tablename__ = TargetTable.RELATIONAL_OPERATORS.table
    __table_args__ = {"schema": TargetTable.RELATIONAL_OPERATORS.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    field_dependencies: Mapped[List["FieldDependency"]] = relationship(
        "FieldDependency", back_populates="operator_type"
    )
    section_dependencies: Mapped[List["SectionDependency"]] = relationship(
        "SectionDependency", back_populates="operator_type"
    )


class RuleType(Base):
    """Rule type for field rules. aka minimum length, maximum length, regex, etc."""

    __tablename__ = TargetTable.RULE_TYPES.table
    __table_args__ = {"schema": TargetTable.RULE_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    field_rules: Mapped[List["FieldRule"]] = relationship(
        "FieldRule", back_populates="rule"
    )


class SubmissionStatusType(Base):
    __tablename__ = TargetTable.SUBMISSION_STATUS_TYPES.table
    __table_args__ = {"schema": TargetTable.SUBMISSION_STATUS_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    submissions: Mapped[List["Submission"]] = relationship(
        "Submission", back_populates="status"
    )
