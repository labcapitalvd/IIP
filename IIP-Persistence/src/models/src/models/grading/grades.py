from decimal import Decimal

from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_decimal,
    column_updated_at,
    column_fk,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class Grade(Base):
    __tablename__ = TargetTable.GRADES.table
    __table_args__ = {"schema": TargetTable.GRADES.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", ondelete="SET NULL"
    )
    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id", ondelete="SET NULL"
    )
    criteria_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.CRITERIA.fq_name}.id", ondelete="SET NULL"
    )

    grade: Mapped[Decimal] = column_decimal(precision=5, scale=2)

    
    updated_at: Mapped[datetime] = column_updated_at()
