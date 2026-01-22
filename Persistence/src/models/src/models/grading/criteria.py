from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_short_text,
    column_decimal,
    column_enum,
    column_integer,
    column_uuid,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class Criteria(Base):
    __tablename__ = TargetTable.CRITERIA.table
    __table_args__ = {"schema": TargetTable.CRITERIA.schema}

    target: Mapped[TargetTable] = column_enum(TargetTable)
    target_id: Mapped[UUID] = column_uuid()
    description: Mapped[str] = column_short_text()
    weight: Mapped[Decimal] = column_decimal()
    display_order: Mapped[int] = column_integer(default=0)
