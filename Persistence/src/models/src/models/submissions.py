from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from shared_db import (
    Base,
    column_bool,
    column_date,
    column_decimal,
    column_fk,
    column_integer,
    column_long_text,
    column_short_text,
    column_updated_at,
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
    __mapper_args__ = {"polymorphic_on": "type_id"}

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
    type_id: Mapped[UUID] = column_fk(target=f"{TargetTable.FIELD_TYPES.fq_name}.id")

    updated_at: Mapped[datetime] = column_updated_at()

    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="answers"
    )
    field: Mapped["Field"] = relationship("Field", back_populates="answers")


class AnswerBoolean(Answer):
    __tablename__ = TargetTable.ANSWERS_BOOLEAN.table
    __table_args__ = {"schema": TargetTable.ANSWERS_BOOLEAN.schema}
    __mapper_args__ = {"polymorphic_identity": "boolean"}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

    value: Mapped[bool] = column_bool()

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="bool_answer"
    )  # adjust name for each type


class AnswerCardEntry(Answer):
    __tablename__ = TargetTable.ANSWERS_CARD_ENTRY.table
    __table_args__ = {"schema": TargetTable.ANSWERS_CARD_ENTRY.schema}
    __mapper_args__ = {"polymorphic_identity": "AnswerCardEntry"}

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


class AnswerDate(Answer):
    __tablename__ = TargetTable.ANSWERS_DATE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_DATE.schema}
    __mapper_args__ = {"polymorphic_identity": "AnswerDate"}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

    value: Mapped[date] = column_date(nullable=True)

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship("Answer", back_populates="date_answer")


class AnswerFile(Answer):
    __tablename__ = TargetTable.ANSWERS_FILE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_FILE.schema}
    __mapper_args__ = {"polymorphic_identity": "AnswerFile"}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

    value_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id",
        ondelete="CASCADE",
        unique=False,
        nullable=True,
    )

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship("Answer", back_populates="file_answer")


class AnswerMultiChoice(Answer):
    __tablename__ = TargetTable.ANSWERS_MULTI_CHOICE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_MULTI_CHOICE.schema}
    __mapper_args__ = {"polymorphic_identity": "AnswerMultiChoice"}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

    updated_at: Mapped[datetime] = column_updated_at()

    option_links: Mapped[list["MultiChoiceOptionLink"]] = relationship(
        "MultiChoiceOptionLink", back_populates="answer", cascade="all, delete-orphan"
    )
    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="multi_choice_answer"
    )  # adjust name for each type


class AnswerNumeric(Answer):
    __tablename__ = TargetTable.ANSWERS_NUMERIC.table
    __table_args__ = {"schema": TargetTable.ANSWERS_NUMERIC.schema}
    __mapper_args__ = {"polymorphic_identity": "AnswerNumeric"}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

    value: Mapped[Decimal] = column_decimal()

    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="number_answer"
    )  # adjust name for each type


class AnswerSingleChoice(Answer):
    __tablename__ = TargetTable.ANSWERS_SINGLE_CHOICE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_SINGLE_CHOICE.schema}
    __mapper_args__ = {"polymorphic_identity": "AnswerSingleChoice"}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

    value_id: Mapped[UUID] = column_fk(target=f"{TargetTable.FIELD_CHOICES.fq_name}.id")

    updated_at: Mapped[datetime] = column_updated_at()

    choice: Mapped["FieldChoice"] = relationship(
        "FieldChoice", back_populates="answer_link"
    )
    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="single_choice_answer"
    )  # adjust name for each type


class AnswerText(Answer):
    __tablename__ = TargetTable.ANSWERS_TEXT.table
    __table_args__ = {"schema": TargetTable.ANSWERS_TEXT.schema}
    __mapper_args__ = {"polymorphic_identity": "AnswerText"}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

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
    card_entries: Mapped["AnswerCardEntry"] = relationship(
        "CardEntry", back_populates="submission"
    )
    answers: Mapped["Answer"] = relationship("Answer", back_populates="submission")
