import importlib
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import foreign
from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_bool,
    column_fk,
    column_long_text,
    column_short_text,
    column_updated_at,
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

criteria_module = importlib.import_module("models.grading.criteria")
Criteria = criteria_module.Criteria


class Question(Base):
    __tablename__ = TargetTable.QUESTIONS.table
    __table_args__ = {"schema": TargetTable.QUESTIONS.schema}

    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="SET NULL"
    )
    section_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id", ondelete="SET NULL"
    )
    is_loop: Mapped[bool] = column_bool()
    file_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id", ondelete="CASCADE", nullable=True
    )

    title: Mapped[str] = column_short_text(255)
    description: Mapped[str] = column_long_text()
    helper: Mapped[str] = column_long_text(nullable=True)
    display_order: Mapped[int] = column_integer(default=0)
    required: Mapped[bool] = column_bool()

    
    updated_at: Mapped[datetime] = column_updated_at()

    section: Mapped["Section"] = relationship("Section", back_populates="questions")
    field_groups: Mapped[List["FieldGroup"]] = relationship(
        "FieldGroup", back_populates="question"
    )
    card_templates: Mapped[List["CardTemplate"]] = relationship(
        "CardTemplate", back_populates="question"
    )

    criteria: Mapped[List["Criteria"]] = relationship(
        "Criteria",
        primaryjoin=lambda: and_(
            foreign(Criteria.target_id) == Question.id,
            Criteria.target == TargetTable.QUESTIONS.table,
        ),
        viewonly=True,
        overlaps="criteria",
    )
