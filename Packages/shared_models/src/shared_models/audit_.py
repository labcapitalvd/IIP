from datetime import datetime
from uuid import UUID
from enum import Enum

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_enum,
    column_long_text,
    column_short_text,
    column_updated_at,
    column_fk,
    column_uuid,
    generate_table_enum,
)
from shared_models.targets import CoreTargetTable

from .targets import CoreTargetTable as TargetTable

TargetTableEnum = generate_table_enum("TargetTableEnum", CoreTargetTable, TargetTable)

class LogActionType(Base):
    __tablename__ = TargetTable.LOG_ACTION_TYPES.table
    __table_args__ = {"schema": TargetTable.LOG_ACTION_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()


class ActivityLog(Base):
    __tablename__ = TargetTable.LOGS.table
    __table_args__ = {"schema": TargetTable.LOGS.schema}

    user_id: Mapped[UUID] = column_fk(target=f"{TargetTable.USERS.fq_name}.id")
    log_action_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.LOG_ACTION_TYPES.fq_name}.id"
    )

    target: Mapped[Enum] = column_enum(TargetTableEnum)
    target_id: Mapped[UUID] = column_uuid()

    description: Mapped[str] = column_long_text(nullable=True)

    timestamp: Mapped[datetime] = column_updated_at()
