from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_short_text,
    column_updated_at,
    column_fk,
)

from ...targets import CoreTargetTable as TargetTable

class UserDetails(Base):
    __tablename__ = TargetTable.USER_DETAILS.table
    __table_args__ = {"schema": TargetTable.USER_DETAILS.schema}

    user_id: Mapped[UUID] = column_fk(f"{TargetTable.USERS.fq_name}.id", unique=True)

    name: Mapped[str] = column_short_text(length=255, nullable=False)
    phone: Mapped[str] = column_short_text(length=50, nullable=True)
    email_pro: Mapped[str] = column_short_text(length=255, unique=True, nullable=False)
    job_title: Mapped[str] = column_short_text(length=255, nullable=True)
    area: Mapped[str] = column_short_text(length=255, nullable=True)
    
    updated_at: Mapped[datetime] = column_updated_at()
