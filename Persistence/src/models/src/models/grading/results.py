from decimal import Decimal

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_fk,
    column_decimal,
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


class Result(Base):
    __tablename__ = TargetTable.RESULTS.table
    __table_args__ = {"schema": TargetTable.RESULTS.schema}

    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id"
    )

    final_score: Mapped[Decimal] = column_decimal(nullable=False)
    
    updated_at: Mapped[datetime] = column_updated_at()
