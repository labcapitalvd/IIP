from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from shared.db import (
    Base,
    column_bool,
    column_created_at,
    column_date,
    column_decimal,
    column_fk,
    column_integer,
    column_long_text,
    column_short_text,
    column_updated_at,
)
from shared.enums import FieldTypesEnum as AnswerType
from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .targets import TargetTable

if TYPE_CHECKING:
    from .files import File
    from .forms import CardTemplate, Field, FieldChoice
    from .links import MultiChoiceOptionLink, UserSubmissionLink
    from .reference import SubmissionStatusType


class Answer(Base):
    """
    Base polymorphic table for all captured values.
    """

    __tablename__ = TargetTable.ANSWERS.table
    __table_args__ = (
        Index("idx_answers_submission_field", "submission_id", "field_id"),
        {"schema": TargetTable.ANSWERS.schema},
    )
    __mapper_args__ = {"polymorphic_on": "discriminator"}

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
        use_alter=True,
        name="fk_answers_card_entry_instance",
    )
    discriminator: Mapped[str] = column_short_text(length=50, nullable=False)
    updated_at: Mapped[datetime] = column_updated_at()

    # Relationships
    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="answers"
    )
    field: Mapped["Field"] = relationship("Field", back_populates="answers")
    card_entry: Mapped[Optional["AnswerCardEntry"]] = relationship(
        "AnswerCardEntry",
        foreign_keys=[card_entry_id],
        back_populates="child_answers",
        post_update=True,
    )


class AnswerBoolean(Answer):
    __tablename__ = TargetTable.ANSWERS_BOOLEAN.table
    __table_args__ = {"schema": TargetTable.ANSWERS_BOOLEAN.schema}
    __mapper_args__ = {"polymorphic_identity": AnswerType.BOOLEAN.value}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    value: Mapped[bool] = column_bool()


class AnswerCardEntry(Answer):
    """
    A concrete answer item representing an instantiated card boundary block.
    """

    __tablename__ = TargetTable.ANSWERS_CARD_ENTRY.table
    __table_args__ = {"schema": TargetTable.ANSWERS_CARD_ENTRY.schema}

    id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TargetTable.ANSWERS.fq_name}.id", ondelete="CASCADE"),
        primary_key=True,
        use_existing_column=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": AnswerType.CARD.value,
        "inherit_condition": (
            lambda: (
                Base.metadata.tables[TargetTable.ANSWERS_CARD_ENTRY.fq_name].c.id
                == Base.metadata.tables[TargetTable.ANSWERS.fq_name].c.id
            )
        ),
    }

    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id", ondelete="CASCADE"
    )
    card_template_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.CARD_TEMPLATES.fq_name}.id",
        ondelete="CASCADE",
        nullable=False,
    )
    title: Mapped[str] = column_short_text(length=255)
    card_index: Mapped[int] = column_integer(default=0)

    # Relationships
    card_template: Mapped["CardTemplate"] = relationship(
        "CardTemplate", back_populates="card_entries"
    )

    child_answers: Mapped[List["Answer"]] = relationship(
        "Answer", foreign_keys="Answer.card_entry_id", back_populates="card_entry"
    )


class AnswerDate(Answer):
    __tablename__ = TargetTable.ANSWERS_DATE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_DATE.schema}
    __mapper_args__ = {"polymorphic_identity": AnswerType.DATE.value}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    value: Mapped[date] = column_date(nullable=True)


class AnswerFile(Answer):
    __tablename__ = TargetTable.ANSWERS_FILE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_FILE.schema}
    __mapper_args__ = {"polymorphic_identity": AnswerType.FILE.value}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    value_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id", ondelete="CASCADE", nullable=True
    )

    file: Mapped[Optional["File"]] = relationship("File")


class AnswerMultiChoice(Answer):
    __tablename__ = TargetTable.ANSWERS_MULTI_CHOICE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_MULTI_CHOICE.schema}
    __mapper_args__ = {"polymorphic_identity": AnswerType.MULTI_CHOICE.value}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    option_links: Mapped[List["MultiChoiceOptionLink"]] = relationship(
        "MultiChoiceOptionLink", back_populates="answer", cascade="all, delete-orphan"
    )


class AnswerNumeric(Answer):
    __tablename__ = TargetTable.ANSWERS_NUMERIC.table
    __table_args__ = {"schema": TargetTable.ANSWERS_NUMERIC.schema}
    __mapper_args__ = {"polymorphic_identity": AnswerType.NUMERIC.value}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

    value: Mapped[Decimal] = column_decimal()


class AnswerSingleChoice(Answer):
    __tablename__ = TargetTable.ANSWERS_SINGLE_CHOICE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_SINGLE_CHOICE.schema}
    __mapper_args__ = {"polymorphic_identity": AnswerType.SINGLE_CHOICE.value}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    value_id: Mapped[UUID] = column_fk(target=f"{TargetTable.FIELD_CHOICES.fq_name}.id")

    choice: Mapped["FieldChoice"] = relationship(
        "FieldChoice", back_populates="answer_link"
    )


class AnswerText(Answer):
    __tablename__ = TargetTable.ANSWERS_TEXT.table
    __table_args__ = {"schema": TargetTable.ANSWERS_TEXT.schema}
    __mapper_args__ = {"polymorphic_identity": AnswerType.TEXT.value}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    value: Mapped[str] = column_long_text()


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
        target=f"{TargetTable.SUBMISSION_STATUS_TYPES.fq_name}.id", ondelete="SET NULL"
    )

    created_at: Mapped[datetime] = column_created_at()
    updated_at: Mapped[datetime] = column_updated_at()

    # Relationships
    status: Mapped["SubmissionStatusType"] = relationship(
        "SubmissionStatusType", back_populates="submissions"
    )
    user_links: Mapped[List["UserSubmissionLink"]] = relationship(
        "UserSubmissionLink", back_populates="submission"
    )

    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        primaryjoin="Submission.id == Answer.submission_id",
        back_populates="submission",
        cascade="all, delete-orphan",
    )

    # Updated viewonly collection to isolate instanced canvas groupings safely
    card_entries: Mapped[List["AnswerCardEntry"]] = relationship(
        "AnswerCardEntry",
        primaryjoin="and_(Submission.id == AnswerCardEntry.submission_id, AnswerCardEntry.discriminator == 'CARD')",
        viewonly=True,
    )
