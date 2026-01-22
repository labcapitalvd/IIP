from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_fk, column_updated_at

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class SingleChoiceAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_SINGLE_CHOICE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_SINGLE_CHOICE.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")
    value_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELD_CHOICES.fq_name}.id"
    )

    
    updated_at: Mapped[datetime] = column_updated_at()

    choice: Mapped["FieldChoice"] = relationship(
        "FieldChoice", back_populates="answer_link"
    )
    answer: Mapped["Answer"] = relationship(
        "Answer", back_populates="single_choice_answer"
    )  # adjust name for each type
