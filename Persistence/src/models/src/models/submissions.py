from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from shared_db import (
    Base,
    column_bool,
    column_date,
    column_decimal,
    column_enum,
    column_fk,
    column_integer,
    column_long_text,
    column_short_text,
    column_updated_at,
    column_uuid,
)
from sqlalchemy.orm import Mapped, relationship

from models.targets import TargetTable

if TYPE_CHECKING:
    from .forms import CardTemplate, Field, FieldChoice
    from .links import MultiChoiceOptionLink, UserSubmissionLink
    from .reference import SubmissionStatusType



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


class BooleanAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_BOOLEAN.table
    __table_args__ = {"schema": TargetTable.ANSWERS_BOOLEAN.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")

    value: Mapped[bool] = column_bool()

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="bool_answer"
    )  # adjust name for each type


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


class DateAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_DATE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_DATE.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")

    value: Mapped[date] = column_date(nullable=True)

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship("Answer", back_populates="date_answer")


class FileAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_FILE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_FILE.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")
    value_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id",
        ondelete="CASCADE",
        unique=False,
        nullable=True,
    )

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship("Answer", back_populates="file_answer")


class MultiChoiceAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_MULTI_CHOICE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_MULTI_CHOICE.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")

    updated_at: Mapped[datetime] = column_updated_at()

    option_links: Mapped[list["MultiChoiceOptionLink"]] = relationship(
        "MultiChoiceOptionLink", back_populates="answer", cascade="all, delete-orphan"
    )
    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="multi_choice_answer"
    )  # adjust name for each type


class NumberAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_NUMERIC.table
    __table_args__ = {"schema": TargetTable.ANSWERS_NUMERIC.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")

    value: Mapped[Decimal] = column_decimal()

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="number_answer"
    )  # adjust name for each type


class SingleChoiceAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_SINGLE_CHOICE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_SINGLE_CHOICE.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")
    value_id: Mapped[UUID] = column_fk(target=f"{TargetTable.FIELD_CHOICES.fq_name}.id")

    updated_at: Mapped[datetime] = column_updated_at()

    choice: Mapped["FieldChoice"] = relationship(
        "FieldChoice", back_populates="answer_link"
    )
    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="single_choice_answer"
    )  # adjust name for each type


class TextAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_TEXT.table
    __table_args__ = {"schema": TargetTable.ANSWERS_TEXT.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")

    value: Mapped[str] = column_long_text()

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="text_answer"
    )  # adjust name for each type


class Submission(Base):
    __tablename__ = TargetTable.SUBMISSIONS.table
    __table_args__ = {"schema": TargetTable.SUBMISSIONS.schema}

    actor_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTORS.fq_name}.id", ondelete="SET NULL"
    )
    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="SET NULL"
    )
    status_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSION_STATUS_TYPES.fq_name}.id",
        ondelete="SET NULL",
    )

    updated_at: Mapped[datetime] = column_updated_at()

    status: Mapped["SubmissionStatusType"] = relationship(
        "SubmissionStatusType", back_populates="submission", uselist=False
    )

    user_links: Mapped["UserSubmissionLink"] = relationship(
        "UserSubmissionLink", back_populates="submission"
    )
    card_entries: Mapped["CardEntry"] = relationship(
        "CardEntry", back_populates="submission"
    )
    answers: Mapped["Answer"] = relationship("Answer", back_populates="submission")
