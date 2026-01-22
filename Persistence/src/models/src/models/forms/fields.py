from typing import List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_fk,
    column_updated_at,
    column_bool,
    column_short_text,
    column_long_text,
    column_integer,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class Field(Base):
    __tablename__ = TargetTable.FIELDS.table
    __table_args__ = {"schema": TargetTable.FIELDS.schema}

    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="SET NULL"
    )
    field_group_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELD_GROUPS.fq_name}.id", ondelete="CASCADE"
    )
    field_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELD_TYPES.fq_name}.id", ondelete="CASCADE"
    )

    title: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
    required: Mapped[bool] = column_bool()
    display_order: Mapped[int] = column_integer(default=0)

    
    updated_at: Mapped[datetime] = column_updated_at()

    field_type: Mapped["FieldType"] = relationship(
        "FieldType", back_populates="field", uselist=False
    )
    field_group: Mapped["FieldGroup"] = relationship(
        "FieldGroup", back_populates="fields"
    )
    field_choices: Mapped[List["FieldChoice"]] = relationship(
        "FieldChoice", back_populates="field"
    )
    field_rules: Mapped[List["FieldRule"]] = relationship(
        "FieldRule", back_populates="field"
    )
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="field")
    dependencies_triggered_by_others: Mapped[List["FieldDependency"]] = relationship(
        "FieldDependency",
        foreign_keys="FieldDependency.target_field_id",
        back_populates="target_field"
    )
    dependencies_it_triggers: Mapped[List["FieldDependency"]] = relationship(
        "FieldDependency",
        foreign_keys="FieldDependency.depends_on_field_id",
        back_populates="depends_on_field"
    )
