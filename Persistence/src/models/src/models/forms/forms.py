from typing import List

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_short_text,
    column_long_text,
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


class Form(Base):
    __tablename__ = TargetTable.FORMS.table
    __table_args__ = {"schema": TargetTable.FORMS.schema}

    anno: Mapped[int] = column_integer(unique=True)
    name: Mapped[str] = column_short_text()
    description: Mapped[str] = column_long_text()

    sections: Mapped[List["Section"]] = relationship("Section", back_populates="form")
