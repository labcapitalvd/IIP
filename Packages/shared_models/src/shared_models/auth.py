from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship
from shared_db import (
    Base,
    column_bool,
    column_decimal,
    column_fk,
    column_short_text,
    column_updated_at,
    column_long_text,
    column_datetime,
    column_uuid,
    column_integer,
)

from .targets import CoreTargetTable as TargetTable


class Role(Base):
    """
    name: canonical role code (matches RoleCode enum)
    """

    __tablename__ = TargetTable.ROLES.table
    __table_args__ = {"schema": TargetTable.ROLES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
    user_file_link = relationship("UserFileLink", back_populates="roles")


class UserTier(Base):
    __tablename__ = TargetTable.USER_TIERS.table
    __table_args__ = {"schema": TargetTable.USER_TIERS.schema}

    label: Mapped[str] = column_short_text(50)
    max_file_size: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    storage_quota: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    max_requests_per_minute: Mapped[int] = column_integer()
    priority_level: Mapped[int] = column_integer()

    updated_at: Mapped[datetime] = column_updated_at()

    user = relationship("User", back_populates="tier", uselist=False)


class RefreshSession(Base):
    __tablename__ = TargetTable.REFRESH_SESSIONS.table
    __table_args__ = {"schema": TargetTable.REFRESH_SESSIONS.schema}

    user_id: Mapped[UUID] = column_fk(target=f"{TargetTable.USERS.fq_name}.id")

    jti: Mapped[UUID] = column_uuid()
    refresh_hash: Mapped[str] = column_short_text()

    expires_at: Mapped[datetime] = column_datetime()
    is_active: Mapped[bool] = column_bool()
    user = relationship("User", back_populates="refresh_sessions")


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

    user = relationship("User", back_populates="details", uselist=False)


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

    user = relationship("User", back_populates="profile", uselist=False)
    file = relationship("File", back_populates="profile", uselist=False)


class User(Base):
    __tablename__ = TargetTable.USERS.table
    __table_args__ = {"schema": TargetTable.USERS.schema}

    tier_id: Mapped[UUID] = column_fk(target=f"{TargetTable.USER_TIERS.fq_name}.id")

    username: Mapped[str] = column_short_text(length=32, unique=True)
    email: Mapped[str] = column_short_text(length=100, unique=True)
    password_hash: Mapped[str] = column_short_text()
    is_active: Mapped[bool] = column_bool(default=False)
    is_verified: Mapped[bool] = column_bool(default=False)

    updated_at: Mapped[datetime] = column_updated_at()

    media_usage: Mapped[Decimal] = column_decimal(
        precision=15, scale=0, default=Decimal(0)
    )

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    details = relationship("UserDetails", back_populates="user", uselist=False)
    tier = relationship("UserTier", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    file_links = relationship("UserFileLink", back_populates="user")
    refresh_sessions = relationship("RefreshSession", back_populates="user")
