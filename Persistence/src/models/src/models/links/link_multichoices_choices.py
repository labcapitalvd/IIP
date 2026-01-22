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


class MultiChoiceOptionLink(Base):
    __tablename__ = TargetTable.LINK_CHOICE_MULTICHOICE.table
    __table_args__ = {"schema": TargetTable.LINK_CHOICE_MULTICHOICE.schema}

    choice_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELD_CHOICES.fq_name}.id",
        primary_key=True,
        ondelete="SET NULL",
    )
    multi_choice_answer_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS_MULTI_CHOICE.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    
    updated_at: Mapped[datetime] = column_updated_at()

    choice: Mapped["FieldChoice"] = relationship(
        "FieldChoice", back_populates="answer_links"
    )
    answer: Mapped["MultiChoiceAnswer"] = relationship(
        "MultiChoiceAnswer", back_populates="option_links"
    )
