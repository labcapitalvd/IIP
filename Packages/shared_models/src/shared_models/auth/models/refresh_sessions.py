from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_short_text,
    column_bool,
    column_fk,
    column_datetime,
    column_uuid
)

from ...targets import CoreTargetTable as TargetTable


class RefreshSession(Base):
    __tablename__ = TargetTable.REFRESH_SESSIONS.table
    __table_args__ = {"schema": TargetTable.REFRESH_SESSIONS.schema}

    user_id: Mapped[UUID] = column_fk(target=f"{TargetTable.USERS.fq_name}.id")

    jti: Mapped[UUID] = column_uuid()
    refresh_hash: Mapped[str] = column_short_text()
    
    expires_at: Mapped[datetime] = column_datetime()
    is_active: Mapped[bool] = column_bool()
