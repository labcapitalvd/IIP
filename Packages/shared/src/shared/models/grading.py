from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from shared.db import (
    Base,
    column_decimal,
    column_fk,
    column_integer,
    column_short_text,
    column_updated_at,
    column_long_text,
)
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from .targets import TargetTable

if TYPE_CHECKING:
    from .auth import User
    from .forms import Question
    from .submissions import Answer, AnswerCardEntry, Submission


class Criterion(Base):
    """
    Used to represent the criterion to grade a question.
    """

    __tablename__ = TargetTable.CRITERIA.table
    __table_args__ = (
        UniqueConstraint("question_id", "code", name="uq_criteria_question_id_code"),
        {"schema": TargetTable.CRITERIA.schema},
    )

    # assignment_id: Mapped[UUID] = column_fk(
    #     target=f"{TargetTable.ASSIGNMENTS.fq_name}.id",
    #     ondelete="CASCADE",
    #     nullable=True,
    # )
    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id",
        ondelete="CASCADE",
        nullable=False,
    )
    code: Mapped[str] = column_short_text(length=50)
    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str | None] = column_long_text(nullable=True)
    weight: Mapped[Decimal] = column_decimal(precision=5, scale=2)
    display_order: Mapped[int] = column_integer(default=0)

    max_score: Mapped[Decimal] = column_decimal(
        precision=5, scale=2, default=Decimal("5.00")
    )

    question: Mapped["Question"] = relationship("Question", back_populates="criteria")
    grades: Mapped[List["Grade"]] = relationship(
        "Grade", back_populates="criterion", cascade="all, delete-orphan"
    )


class Grade(Base):
    """
    Used to represent a grade.
    """

    __tablename__ = TargetTable.GRADES.table
    __table_args__ = {"schema": TargetTable.GRADES.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", ondelete="SET NULL"
    )
    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id", ondelete="SET NULL"
    )
    criterion_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.CRITERIA.fq_name}.id", ondelete="SET NULL"
    )
    card_entry_id: Mapped[UUID | None] = column_fk(
        target=f"{TargetTable.ANSWERS_CARD_ENTRY.fq_name}.id",
        ondelete="CASCADE",
        nullable=True,
    )
    answer_id: Mapped[UUID | None] = column_fk(
        target=f"{TargetTable.ANSWERS.fq_name}.id", ondelete="CASCADE", nullable=True
    )

    grade: Mapped[Decimal] = column_decimal(precision=5, scale=2)

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User")
    submission: Mapped["Submission"] = relationship("Submission")
    criterion: Mapped["Criterion"] = relationship("Criterion", back_populates="grades")
    card_entry: Mapped[Optional["AnswerCardEntry"]] = relationship(
        "AnswerCardEntry", foreign_keys=[card_entry_id]
    )
    answer: Mapped[Optional["Answer"]] = relationship(
        "Answer", foreign_keys=[answer_id]
    )


class Result(Base):
    """
    The final aggregated and weighted summary record computed for an individual Submission block.
    """

    __tablename__ = TargetTable.RESULTS.table
    __table_args__ = {"schema": TargetTable.RESULTS.schema}

    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id",
        ondelete="CASCADE",
        unique=True,
    )

    final_score: Mapped[Decimal] = column_decimal(precision=8, scale=2, nullable=False)
    updated_at: Mapped[datetime] = column_updated_at()

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission")
