from typing import List

from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_short_text, column_long_text

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class SectionType(Base):
    __tablename__ = TargetTable.SECTION_TYPES.table
    __table_args__ = {"schema": TargetTable.SECTION_TYPES.schema}

    label: Mapped[str] = column_short_text(255)
    description: Mapped[str] = column_long_text()

    sections: Mapped[List["Section"]] = relationship(
        "Section", back_populates="type"
    )