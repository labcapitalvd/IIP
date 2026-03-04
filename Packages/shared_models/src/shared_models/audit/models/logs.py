from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_enum,
    column_long_text,
    column_updated_at,
    column_fk,
    column_uuid,
)

from ...targets import CoreTargetTable as TargetTable


class ActivityLog(Base):
    __tablename__ = TargetTable.LOGS.table
    __table_args__ = {"schema": TargetTable.LOGS.schema}

    user_id: Mapped[UUID] = column_fk(target=f"{TargetTable.USERS.fq_name}.id")
    log_action_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.LOG_ACTION_TYPES.fq_name}.id"
    )

    target: Mapped[TargetTable] = column_enum(TargetTable)
    target_id: Mapped[UUID] = column_uuid()

    description: Mapped[str] = column_long_text(nullable=True)

    timestamp: Mapped[datetime] = column_updated_at()
