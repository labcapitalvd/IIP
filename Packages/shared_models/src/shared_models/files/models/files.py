from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from shared_db import (
    Base,
    column_short_text,
    column_updated_at,
    column_fk,
    column_decimal,
)

from ...targets import CoreTargetTable as TargetTable

class File(Base):
    __tablename__ = TargetTable.FILES.table
    __table_args__ = {"schema": TargetTable.FILES.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", ondelete="CASCADE"
    )
    file_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILE_TYPES.fq_name}.id", ondelete="CASCADE"
    )

    filename: Mapped[str] = column_short_text(length=64)
    filepath: Mapped[str] = column_short_text(length=255)
    filehash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    filesize: Mapped[Decimal] = column_decimal(precision=15, scale=0)

    
    updated_at: Mapped[datetime] = column_updated_at()
