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
    column_created_at,
    column_updated_at,
)
from sqlalchemy.orm import Mapped, column_property, relationship

from shared_enums import FieldTypesEnum as AnswerType
from .targets import TargetTable

if TYPE_CHECKING:
    from .forms import CardTemplate, Field, FieldChoice
    from .links import MultiChoiceOptionLink, UserSubmissionLink
    from .reference import SubmissionStatusType


class Answer(Base):
    __tablename__ = TargetTable.ANSWERS.table
    __table_args__ = {"schema": TargetTable.ANSWERS.schema}
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
    # discriminator is required by SQLAlchemy for Joined Table Inheritance because
    # our Python identities are strings (e.g. "AnswerBoolean") but type_id is a UUID.
    # It acts as the local type identifier.
    discriminator: Mapped[str] = column_short_text(length=50, nullable=False)

    updated_at: Mapped[datetime] = column_updated_at()

    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="answers"
    )
    field: Mapped["Field"] = relationship("Field", back_populates="answers")
    card_entry: Mapped[Optional["AnswerCardEntry"]] = relationship(
        "AnswerCardEntry",
        foreign_keys=[card_entry_id],
        back_populates="answers",
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
    __tablename__ = TargetTable.ANSWERS_CARD_ENTRY.table
    __table_args__ = {"schema": TargetTable.ANSWERS_CARD_ENTRY.schema}
    __mapper_args__ = {
        "polymorphic_identity": AnswerType.CARD.value,
        "inherit_condition": id == Answer.id,
    }

    id: Mapped[UUID] = column_property(
        column_fk(
            target=f"{TargetTable.ANSWERS.fq_name}.id",
            primary_key=True,
            ondelete="CASCADE",
        ),
        Answer.id,
    )

    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id", ondelete="CASCADE"
    )
    card_template_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.CARD_TEMPLATES.fq_name}.id",
        ondelete="CASCADE",
        nullable=False,
    )

    title: Mapped[str] = column_short_text(length=255)
    card_index: Mapped[int] = column_integer()

    card_template: Mapped["CardTemplate"] = relationship(
        "CardTemplate", back_populates="card_entries"
    )
    answers: Mapped[List["Answer"]] = relationship(
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

    value_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id",
        ondelete="CASCADE",
        unique=False,
        nullable=True,
    )


class AnswerMultiChoice(Answer):
    __tablename__ = TargetTable.ANSWERS_MULTI_CHOICE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_MULTI_CHOICE.schema}
    __mapper_args__ = {"polymorphic_identity": AnswerType.MULTI_CHOICE.value}

    id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )

    option_links: Mapped[list["MultiChoiceOptionLink"]] = relationship(
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
        target=f"{TargetTable.SUBMISSION_STATUS_TYPES.fq_name}.id",
        ondelete="SET NULL",
    )
    created_at: Mapped[datetime] = column_created_at()
    updated_at: Mapped[datetime] = column_updated_at()

    status: Mapped["SubmissionStatusType"] = relationship(
        "SubmissionStatusType", back_populates="submission", uselist=False
    )

    user_links: Mapped["UserSubmissionLink"] = relationship(
        "UserSubmissionLink", back_populates="submission"
    )
    answers: Mapped[List["Answer"]] = relationship(
        "Answer", back_populates="submission", cascade="all, delete-orphan"
    )
    card_entries: Mapped[List["AnswerCardEntry"]] = relationship(
        "AnswerCardEntry",
        back_populates="submission",
        viewonly=True,
        foreign_keys="Answer.submission_id",
    )
