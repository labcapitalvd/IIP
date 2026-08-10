from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Index  # Add import if missing
from sqlalchemy.orm import Mapped, relationship

from shared.db import (
    Base,
    column_decimal,
    column_enum,
    column_fk,
    column_short_text,
    column_updated_at,
    column_uuid,
    column_long_text,
)

from shared.enums import VisibilityScope

from .targets import TargetTable


if TYPE_CHECKING:
    from .actors import Actor
    from .auth import User


class FileType(Base):
    """
    Used to represent the different file types supported by the platform.
    """

    __tablename__ = TargetTable.FILE_TYPES.table
    __table_args__ = {"schema": TargetTable.FILE_TYPES.schema}

    code: Mapped[str] = column_short_text(length=50, unique=True)
    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str | None] = column_long_text(nullable=True)
    mime_type: Mapped[str] = column_short_text(length=255)
    extension: Mapped[str] = column_short_text(length=255)
    category: Mapped[str] = column_short_text(length=255)
    max_size: Mapped[Decimal] = column_decimal(precision=15, scale=0)

    files: Mapped[list["File"]] = relationship("File", back_populates="type")


class File(Base):
    """
    Low-level immutable storage record representing physical bytes on disk/S3.
    """

    __tablename__ = TargetTable.FILES.table
    __table_args__ = {"schema": TargetTable.FILES.schema}

    file_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILE_TYPES.fq_name}.id", ondelete="CASCADE"
    )
    uploaded_by_user_id: Mapped[UUID | None] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", ondelete="SET NULL", nullable=True
    )

    filename: Mapped[str] = column_short_text(length=64)
    filepath: Mapped[str] = column_short_text(length=255)
    filehash: Mapped[str] = column_short_text(
        length=64, unique=True, index=True, nullable=False
    )
    filesize: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    updated_at: Mapped[datetime] = column_updated_at()

    type: Mapped["FileType"] = relationship("FileType", back_populates="files")
    uploader: Mapped["User | None"] = relationship("User")
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="file", cascade="all, delete-orphan"
    )


class Attachment(Base):
    """
    Contextual attachment linking physical files to application entities.
    """

    __tablename__ = TargetTable.ATTACHMENTS.table
    __table_args__ = (
        Index("idx_attachment_entity", "entity_type", "entity_id"),
        {"schema": TargetTable.ATTACHMENTS.schema},
    )

    file_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id", ondelete="CASCADE"
    )

    # WHERE 2: Add ondelete="SET NULL" to these foreign keys
    user_id: Mapped[UUID | None] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", nullable=True, ondelete="CASCADE"
    )
    actor_id: Mapped[UUID | None] = column_fk(
        target=f"{TargetTable.ACTORS.fq_name}.id", nullable=True, ondelete="SET NULL"
    )

    entity_type: Mapped[str | None] = column_short_text(length=50, nullable=True)
    entity_id: Mapped[UUID | None] = column_uuid(nullable=True)
    visibility: Mapped["VisibilityScope"] = column_enum(
        VisibilityScope,
        default=VisibilityScope.PRIVATE,
        name="visibility_scope",
    )
    updated_at: Mapped[datetime] = column_updated_at()

    file: Mapped["File"] = relationship("File", back_populates="attachments")
    user: Mapped["User | None"] = relationship("User", back_populates="attachments")
    actor: Mapped["Actor | None"] = relationship("Actor", back_populates="attachments")
