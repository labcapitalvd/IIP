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


class FormResult(Base):
    """
    Resultado histórico de una entidad en un formulario (puntos tal como se presentaron en su
    época). Es independiente de los radicados: puede existir sin respuestas cargadas.
    Los valores no se validan contra los pesos del formulario.
    """

    __tablename__ = TargetTable.FORM_RESULTS.table
    __table_args__ = (
        UniqueConstraint("form_id", "actor_id", name="uq_form_results_form_actor"),
        {"schema": TargetTable.FORM_RESULTS.schema},
    )

    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="CASCADE", nullable=False
    )
    actor_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTORS.fq_name}.id", ondelete="CASCADE", nullable=False
    )
    total: Mapped[Optional[Decimal]] = column_decimal(precision=14, scale=4, nullable=True)
    updated_at: Mapped[datetime] = column_updated_at()

    sections: Mapped[List["SectionResult"]] = relationship(
        "SectionResult", back_populates="form_result", cascade="all, delete-orphan"
    )


class SectionResult(Base):
    """Puntaje de una entidad en un componente, variable o indicador de un formulario."""

    __tablename__ = TargetTable.SECTION_RESULTS.table
    __table_args__ = (
        UniqueConstraint(
            "form_result_id", "section_id", name="uq_section_results_result_section"
        ),
        {"schema": TargetTable.SECTION_RESULTS.schema},
    )

    form_result_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORM_RESULTS.fq_name}.id", ondelete="CASCADE", nullable=False
    )
    section_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id", ondelete="CASCADE", nullable=False
    )
    score: Mapped[Optional[Decimal]] = column_decimal(precision=14, scale=4, nullable=True)

    form_result: Mapped["FormResult"] = relationship("FormResult", back_populates="sections")


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
