from datetime import datetime
from decimal import Decimal
from uuid import UUID

from shared_db import (
    Base,
    column_decimal,
    column_fk,
    column_integer,
    column_short_text,
    column_updated_at,
)
from sqlalchemy.orm import Mapped

from .targets import TargetTable


class Criterion(Base):
    __tablename__ = TargetTable.CRITERIA.table
    __table_args__ = {"schema": TargetTable.CRITERIA.schema}

    # assignment_id: Mapped[UUID] = column_fk(
    #     target=f"{TargetTable.ASSIGNMENTS.fq_name}.id",
    #     ondelete="CASCADE",
    #     nullable=True,
    # )
    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id",
        ondelete="CASCADE",
        nullable=True,
    )
    description: Mapped[str] = column_short_text()
    weight: Mapped[Decimal] = column_decimal()
    display_order: Mapped[int] = column_integer(default=0)


class Grade(Base):
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

    grade: Mapped[Decimal] = column_decimal(precision=5, scale=2)

    updated_at: Mapped[datetime] = column_updated_at()


class Result(Base):
    __tablename__ = TargetTable.RESULTS.table
    __table_args__ = {"schema": TargetTable.RESULTS.schema}

    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id"
    )

    final_score: Mapped[Decimal] = column_decimal(nullable=False)

    updated_at: Mapped[datetime] = column_updated_at()
