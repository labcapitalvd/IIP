from typing import List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_fk,
    column_short_text,
    column_integer,
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


class CardEntry(Base):
    __tablename__ = TargetTable.ANSWERS_CARD_ENTRY.table
    __table_args__ = {"schema": TargetTable.ANSWERS_CARD_ENTRY.schema}

    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id", ondelete="CASCADE"
    )
    card_template_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.CARD_TEMPLATES.fq_name}.id",
        ondelete="CASCADE",
        nullable=False,
    )
    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id",
        ondelete="CASCADE",
        nullable=False,
    )

    title: Mapped[str] = column_short_text(length=255)
    card_index: Mapped[int] = column_integer()

    
    updated_at: Mapped[datetime] = column_updated_at()

    card_template: Mapped["CardTemplate"] = relationship(
        "CardTemplate", back_populates="card_entries"
    )
    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="card_entries"
    )
    answers: Mapped[List["Answer"]] = relationship(
        "Answer", back_populates="card_entry", cascade="all, delete-orphan"
    )
