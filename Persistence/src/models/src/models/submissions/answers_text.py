from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_long_text,
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


class TextAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_TEXT.table
    __table_args__ = {"schema": TargetTable.ANSWERS_TEXT.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")

    value: Mapped[str] = column_long_text()

    
    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="text_answer"
    )  # adjust name for each type
