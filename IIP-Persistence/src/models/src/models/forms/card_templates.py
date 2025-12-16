import importlib
from typing import List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import and_
from sqlalchemy.orm import remote, foreign

from shared_db import (
    Base,
    column_short_text,
    column_fk,
    column_updated_at,
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

from .questions import Question

criteria_module = importlib.import_module("models.grading.criteria")
Criteria = criteria_module.Criteria


class CardTemplate(Base):
    __tablename__ = TargetTable.CARD_TEMPLATES.table
    __table_args__ = {"schema": TargetTable.CARD_TEMPLATES.schema}

    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id", ondelete="CASCADE"
    )

    title: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
    helper: Mapped[str] = column_long_text(nullable=True)

    
    updated_at: Mapped[datetime] = column_updated_at()

    question: Mapped["Question"] = relationship(
        "Question", back_populates="card_templates"
    )
    field_groups: Mapped[List["FieldGroup"]] = relationship(
        "FieldGroup", back_populates="card_template"
    )
    card_entries: Mapped[List["CardEntry"]] = relationship(
        "CardEntry", back_populates="card_template", cascade="all, delete-orphan"
    )

    criteria: Mapped[List["Criteria"]] = relationship(
        "Criteria",
        primaryjoin=lambda: and_(
            foreign(Criteria.target_id) == remote(Question.id),
            Criteria.target == TargetTable.QUESTIONS.table,
        ),
        viewonly=True,
        overlaps="criteria",
    )
