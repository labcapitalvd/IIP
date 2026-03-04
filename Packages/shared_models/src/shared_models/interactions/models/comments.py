from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_enum,
    column_fk,
    column_long_text,
    column_updated_at,
    column_uuid,
    column_short_text,
)

from ...targets import CoreTargetTable as TargetTable

class Comment(Base):
    __tablename__ = TargetTable.COMMENTS.table
    __table_args__ = {"schema": TargetTable.COMMENTS.schema}

    user_id: Mapped[UUID] = column_fk(target=f"{TargetTable.USERS.fq_name}.id")
    comment_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.COMMENT_TYPES.fq_name}.id", ondelete="CASCADE"
    )

    target: Mapped[TargetTable] = column_enum(TargetTable)
    target_id: Mapped[UUID] = column_uuid()

    label: Mapped[str] = column_short_text(255)
    content: Mapped[str] = column_long_text()

    
    updated_at: Mapped[datetime] = column_updated_at()
