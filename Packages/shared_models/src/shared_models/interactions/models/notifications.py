from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_long_text,
    column_updated_at,
    column_fk,
    column_short_text,
    column_bool,
)

from ...targets import CoreTargetTable as TargetTable

class Notification(Base):
    __tablename__ = TargetTable.NOTIFICATIONS.table
    __table_args__ = {"schema": TargetTable.NOTIFICATIONS.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", ondelete="CASCADE"
    )
    notification_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.NOTIFICATION_TYPES.fq_name}.id", ondelete="CASCADE"
    )

    label: Mapped[str] = column_short_text(255)
    content: Mapped[str] = column_long_text()

    is_read: Mapped[bool] = column_bool(default=False)

    
    updated_at: Mapped[datetime] = column_updated_at()
