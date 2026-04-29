from typing import TYPE_CHECKING

from shared_db import (
    Base,
    column_long_text,
    column_short_text,
)
from sqlalchemy.orm import Mapped, relationship

from models.targets import TargetTable

if TYPE_CHECKING:
    from .forms import Field
    from .rules import FieldDependency, FieldRule, SectionDependency
    from .submissions import Submission



class FieldType(Base):
    __tablename__ = TargetTable.FIELD_TYPES.table
    __table_args__ = {"schema": TargetTable.FIELD_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    field: Mapped["Field"] = relationship(
        "Field", back_populates="field_type", uselist=False
    )


class RelationalOperator(Base):
    __tablename__ = TargetTable.RELATIONAL_OPERATORS.table
    __table_args__ = {"schema": TargetTable.RELATIONAL_OPERATORS.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    field_dependency: Mapped["FieldDependency"] = relationship(
        "FieldDependency", back_populates="operator_type", uselist=False
    )

    section_dependency: Mapped["SectionDependency"] = relationship(
        "SectionDependency", back_populates="operator_type", uselist=False
    )


class RuleType(Base):
    """Rule type for field rules. aka minimum length, maximum length, regex, etc."""

    __tablename__ = TargetTable.RULE_TYPES.table
    __table_args__ = {"schema": TargetTable.RULE_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    field_rule: Mapped["FieldRule"] = relationship(
        "FieldRule", back_populates="rule", uselist=False
    )


class SubmissionStatusType(Base):
    __tablename__ = TargetTable.SUBMISSION_STATUS_TYPES.table
    __table_args__ = {"schema": TargetTable.SUBMISSION_STATUS_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="status", uselist=False
    )
