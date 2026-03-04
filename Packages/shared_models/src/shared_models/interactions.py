from enum import Enum
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
    column_bool,
    generate_table_enum
)
from shared_models.targets import CoreTargetTable

from .targets import CoreTargetTable as TargetTable

TargetTableEnum = generate_table_enum("TargetTableEnum", CoreTargetTable, TargetTable)


class NotificationType(Base):
    __tablename__ = TargetTable.NOTIFICATION_TYPES.table
    __table_args__ = {"schema": TargetTable.NOTIFICATION_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()


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


class CommentType(Base):
    __tablename__ = TargetTable.COMMENT_TYPES.table
    __table_args__ = {"schema": TargetTable.COMMENT_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()


class Comment(Base):
    __tablename__ = TargetTable.COMMENTS.table
    __table_args__ = {"schema": TargetTable.COMMENTS.schema}

    user_id: Mapped[UUID] = column_fk(target=f"{TargetTable.USERS.fq_name}.id")
    comment_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.COMMENT_TYPES.fq_name}.id", ondelete="CASCADE"
    )

    target: Mapped[Enum] = column_enum(TargetTableEnum)
    target_id: Mapped[UUID] = column_uuid()

    label: Mapped[str] = column_short_text(255)
    content: Mapped[str] = column_long_text()

    
    updated_at: Mapped[datetime] = column_updated_at()
