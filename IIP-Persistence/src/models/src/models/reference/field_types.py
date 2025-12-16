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


class FieldType(Base):
    __tablename__ = TargetTable.FIELD_TYPES.table
    __table_args__ = {"schema": TargetTable.FIELD_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    field: Mapped["Field"] = relationship(
        "Field", back_populates="field_type", uselist=False
    )
