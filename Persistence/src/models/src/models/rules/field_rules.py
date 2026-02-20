from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_fk,
    column_short_text,
    column_updated_at,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class FieldRule(Base):
    """Model that assigns validation rules to fields."""
    __tablename__ = TargetTable.FIELD_RULES.table
    __table_args__ = {"schema": TargetTable.FIELD_RULES.schema}

    field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id",
        ondelete="CASCADE"
    )
    rule_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.RULE_TYPES.fq_name}.id",
        ondelete="CASCADE"
    )

    rule_value: Mapped[str] = column_short_text(255)  # JSON string for complex rules
    error_message: Mapped[str] = column_short_text(255)

    
    updated_at: Mapped[datetime] = column_updated_at()

    rule: Mapped["RuleType"] = relationship(
        "RuleType",
        back_populates="field_rule",
        uselist=False
    )

    field: Mapped["Field"] = relationship(
        "Field",
        back_populates="field_rules"
    )
