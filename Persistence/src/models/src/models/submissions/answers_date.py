from datetime import date, datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_date,
    column_fk,
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


class DateAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_DATE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_DATE.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")

    value: Mapped[date] = column_date(nullable=True)

    
    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship("Answer", back_populates="date_answer")
