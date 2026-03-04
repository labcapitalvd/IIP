from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_long_text,
    column_updated_at,
    column_fk,
)

from ...targets import CoreTargetTable as TargetTable

class UserProfile(Base):
    __tablename__ = TargetTable.USER_PROFILES.table
    __table_args__ = {"schema": TargetTable.USER_PROFILES.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", unique=True
    )
    file_id: Mapped[UUID | None] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id",
        ondelete="CASCADE",
        unique=True,
        nullable=True,
    )

    biography: Mapped[str | None] = column_long_text(nullable=True)
    
    updated_at: Mapped[datetime] = column_updated_at()
