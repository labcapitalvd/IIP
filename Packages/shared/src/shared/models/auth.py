from datetime import datetime
from decimal import Decimal
from uuid import UUID

from shared.db import (
    Base,
    column_bool,
    column_datetime,
    column_decimal,
    column_fk,
    column_integer,
    column_long_text,
    column_short_text,
    column_updated_at,
    column_uuid,
)
from sqlalchemy.orm import Mapped, relationship

from .targets import TargetTable


# =====================================================================
# 1. RESOURCE ReBAC ACCESS LEVELS (Scoped to File, Submission, Actor)
# =====================================================================


class AccessLevel(Base):
    """
    Represents entity-scoped access levels (e.g., 'viewer', 'editor', 'evaluator').
    Used in link tables like UserFileLink, UserSubmissionLink, UserActorLink.
    """

    __tablename__ = TargetTable.ACCESS_LEVELS.table
    __table_args__ = {"schema": TargetTable.ACCESS_LEVELS.schema}

    code: Mapped[str] = column_short_text(length=50, unique=True)  # e.g., 'evaluator'
    label: Mapped[str] = column_short_text(length=255)  # e.g., 'Evaluator'
    description: Mapped[str | None] = column_long_text(nullable=True)

    file_links = relationship("UserFileLink", back_populates="access_level")
    submission_links = relationship("UserSubmissionLink", back_populates="access_level")
    actor_links = relationship("UserActorLink", back_populates="access_level")


# =====================================================================
# 2. GLOBAL SYSTEM RBAC (Platform-Wide Roles)
# =====================================================================


class SystemRole(Base):
    """
    Represents global application roles (e.g., 'PlatformAdmin', 'Grader', 'StandardUser').
    """

    __tablename__ = TargetTable.SYSTEM_ROLES.table
    __table_args__ = {"schema": TargetTable.SYSTEM_ROLES.schema}

    code: Mapped[str] = column_short_text(length=50, unique=True)  # e.g., 'admin'
    label: Mapped[str] = column_short_text(length=255)  # e.g., 'Platform Admin'
    description: Mapped[str | None] = column_long_text(nullable=True)

    user_links = relationship("UserSystemRoleLink", back_populates="system_role")


# =====================================================================
# 3. ENTITLEMENTS / TIERS (Quotas & Limits)
# =====================================================================


class UserTier(Base):
    """
    Represents platform tiers and operational quotas/limits.
    """

    __tablename__ = TargetTable.USER_TIERS.table
    __table_args__ = {"schema": TargetTable.USER_TIERS.schema}

    code: Mapped[str] = column_short_text(50, unique=True)  # e.g., 'free', 'pro'
    label: Mapped[str] = column_short_text(50)
    max_file_size: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    storage_quota: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    max_requests_per_minute: Mapped[int] = column_integer()
    priority_level: Mapped[int] = column_integer()

    updated_at: Mapped[datetime] = column_updated_at()

    users: Mapped[list["User"]] = relationship("User", back_populates="tier")


# =====================================================================
# 4. AUTH & PROFILE CORE MODELS
# =====================================================================


class RefreshSession(Base):
    """
    Holds active JWT refresh token sessions.
    """

    __tablename__ = TargetTable.REFRESH_SESSIONS.table
    __table_args__ = {"schema": TargetTable.REFRESH_SESSIONS.schema}

    user_id: Mapped[UUID] = column_fk(target=f"{TargetTable.USERS.fq_name}.id")

    jti: Mapped[UUID] = column_uuid()
    refresh_hash: Mapped[str] = column_short_text()

    expires_at: Mapped[datetime] = column_datetime()
    is_active: Mapped[bool] = column_bool()

    user: Mapped["User"] = relationship("User", back_populates="refresh_sessions")


class UserDetails(Base):
    """
    Additional personal and professional user attributes.
    """

    __tablename__ = TargetTable.USER_DETAILS.table
    __table_args__ = {"schema": TargetTable.USER_DETAILS.schema}

    user_id: Mapped[UUID] = column_fk(f"{TargetTable.USERS.fq_name}.id", unique=True)

    name: Mapped[str] = column_short_text(length=255, nullable=False)
    phone: Mapped[str | None] = column_short_text(length=50, nullable=True)
    email_pro: Mapped[str] = column_short_text(length=255, unique=True, nullable=False)
    job_title: Mapped[str | None] = column_short_text(length=255, nullable=True)
    area: Mapped[str | None] = column_short_text(length=255, nullable=True)

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", back_populates="details", uselist=False)


class UserProfile(Base):
    """
    Public-facing profile and avatar image link.
    """

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

    user: Mapped["User"] = relationship("User", back_populates="profile", uselist=False)
    file = relationship("File", back_populates="profile", uselist=False)


class User(Base):
    """
    Core User identity model.
    """

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

    # Core Relationships
    profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile", back_populates="user", uselist=False
    )
    details: Mapped["UserDetails | None"] = relationship(
        "UserDetails", back_populates="user", uselist=False
    )
    tier: Mapped["UserTier"] = relationship(
        "UserTier", back_populates="users", uselist=False
    )
    refresh_sessions = relationship("RefreshSession", back_populates="user")

    # Global RBAC Links
    system_role_links: Mapped[list["UserSystemRoleLink"]] = relationship(
        "UserSystemRoleLink", back_populates="user"
    )

    # Resource ReBAC Links
    file_links = relationship("UserFileLink", back_populates="user")
    actor_links = relationship("UserActorLink", back_populates="user")
    submission_links = relationship("UserSubmissionLink", back_populates="user")

    # Activity Relationships
    notifications = relationship("Notification", back_populates="user")
    comments = relationship("Comment", back_populates="user")
