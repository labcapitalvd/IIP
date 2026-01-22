from typing import List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_fk,
    column_short_text,
    column_updated_at,
    column_integer,
    column_long_text,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class FieldGroup(Base):
    __tablename__ = TargetTable.FIELD_GROUPS.table
    __table_args__ = {"schema": TargetTable.FIELD_GROUPS.schema}

    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="SET NULL"
    )
    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id", ondelete="CASCADE"
    )
    card_template_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.CARD_TEMPLATES.fq_name}.id",
        ondelete="CASCADE",
        nullable=True,
    )

    title: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
    display_order: Mapped[int] = column_integer(default=0)

    
    updated_at: Mapped[datetime] = column_updated_at()

    question: Mapped["Question"] = relationship(
        "Question", back_populates="field_groups"
    )
    card_template: Mapped["CardTemplate"] = relationship(
        "CardTemplate", back_populates="field_groups"
    )
    fields: Mapped[List["Field"]] = relationship("Field", back_populates="field_group")
