from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_fk,
    column_short_text,
    column_updated_at,
    column_integer,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class FieldChoice(Base):
    __tablename__ = TargetTable.FIELD_CHOICES.table
    __table_args__ = {"schema": TargetTable.FIELD_CHOICES.schema}

    field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id", ondelete="CASCADE"
    )

    title: Mapped[str] = column_short_text(255)
    description: Mapped[str] = column_short_text(255)
    display_order: Mapped[int] = column_integer(default=0)

    
    updated_at: Mapped[datetime] = column_updated_at()

    answer_links: Mapped[list["MultiChoiceOptionLink"]] = relationship(
        "MultiChoiceOptionLink", back_populates="choice"
    )
    answer_link: Mapped["SingleChoiceAnswer"] = relationship(
        "SingleChoiceAnswer", back_populates="choice"
    )
    field: Mapped["Field"] = relationship("Field", back_populates="field_choices")
