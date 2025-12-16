from typing import Optional

from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_fk,
    column_enum,
    column_updated_at,
    column_uuid,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class Answer(Base):
    __tablename__ = TargetTable.ANSWERS.table
    __table_args__ = {"schema": TargetTable.ANSWERS.schema}

    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id",
        ondelete="CASCADE",
        nullable=False,
    )
    field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id", ondelete="CASCADE", nullable=False
    )
    card_entry_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.ANSWERS_CARD_ENTRY.fq_name}.id",
        ondelete="CASCADE",
        nullable=True,
    )

    value_table: Mapped[TargetTable] = column_enum(TargetTable)
    value_id: Mapped[UUID] = column_uuid()

    
    updated_at: Mapped[datetime] = column_updated_at()

    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="answers"
    )
    card_entry: Mapped["CardEntry"] = relationship(
        "CardEntry", back_populates="answers"
    )
    bool_answer: Mapped["BooleanAnswer"] = relationship(
        "BooleanAnswer", back_populates="answer", uselist=False
    )
    date_answer: Mapped["DateAnswer"] = relationship(
        "DateAnswer", back_populates="answer", uselist=False
    )
    file_answer: Mapped["FileAnswer"] = relationship(
        "FileAnswer", back_populates="answer", uselist=False
    )
    multi_choice_answer: Mapped["MultiChoiceAnswer"] = relationship(
        "MultiChoiceAnswer", back_populates="answer", uselist=False
    )
    number_answer: Mapped["NumberAnswer"] = relationship(
        "NumberAnswer", back_populates="answer", uselist=False
    )
    single_choice_answer: Mapped["SingleChoiceAnswer"] = relationship(
        "SingleChoiceAnswer", back_populates="answer", uselist=False
    )
    text_answer: Mapped["TextAnswer"] = relationship(
        "TextAnswer", back_populates="answer", uselist=False
    )

    field: Mapped["Field"] = relationship("Field", back_populates="answers")
