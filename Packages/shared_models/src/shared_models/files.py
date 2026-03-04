from datetime import datetime
from decimal import Decimal
from uuid import UUID

from shared_db import (
    Base,
    column_decimal,
    column_fk,
    column_short_text,
    column_updated_at,
)
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .targets import CoreTargetTable as TargetTable


class FileType(Base):
    __tablename__ = TargetTable.FILE_TYPES.table
    __table_args__ = {"schema": TargetTable.FILE_TYPES.schema}

    label: Mapped[str] = column_short_text(255)
    mime_type: Mapped[str] = column_short_text(length=255)
    extension: Mapped[str] = column_short_text(length=255)
    category: Mapped[str] = column_short_text(length=255)
    max_size: Mapped[Decimal] = column_decimal(precision=15, scale=0)

    file = relationship("File", back_populates="type", uselist=False)


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

    profile = relationship("UserProfile", back_populates="file", uselist=False)
    user_links = relationship("UserFileLink", back_populates="file")
    type = relationship("FileType", back_populates="file", uselist=False)
