from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, relationship

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

from .targets import TargetTable

if TYPE_CHECKING:
    from .files import Attachment
    from .interactions import Comment, Notification
    from .links import (
        ResourceRolePermissionLink,
        SystemRolePermissionLink,
        UserActorLink,
        UserSystemRoleLink,
    )


# =====================================================================
# 1. PERMISSIONS & SCOPED RESOURCE ROLES (ReBAC)
# =====================================================================


class Permission(Base):
    """
    Represents an atomic, granular action key used across API security guards.
    """

    __tablename__ = TargetTable.PERMISSIONS.table
    __table_args__ = {"schema": TargetTable.PERMISSIONS.schema}

    key: Mapped[str] = column_short_text(length=100, unique=True)
    code: Mapped[str] = column_short_text(length=50, unique=True)
    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str | None] = column_long_text(nullable=True)

    system_role_links: Mapped[list["SystemRolePermissionLink"]] = relationship(
        "SystemRolePermissionLink", back_populates="permission"
    )
    resource_role_links: Mapped[list["ResourceRolePermissionLink"]] = relationship(
        "ResourceRolePermissionLink", back_populates="permission"
    )


class ResourceRole(Base):
    """
    Represents an entity-scoped capability bundle (ReBAC role) attached to an Actor.
    """

    __tablename__ = TargetTable.RESOURCE_ROLES.table
    __table_args__ = {"schema": TargetTable.RESOURCE_ROLES.schema}

    code: Mapped[str] = column_short_text(length=50, unique=True)
    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str | None] = column_long_text(nullable=True)

    permission_links: Mapped[list["ResourceRolePermissionLink"]] = relationship(
        "ResourceRolePermissionLink", back_populates="resource_role"
    )
    actor_links: Mapped[list["UserActorLink"]] = relationship(
        "UserActorLink", back_populates="resource_role"
    )


# =====================================================================
# 2. GLOBAL SYSTEM RBAC (Platform-Wide Roles)
# =====================================================================


class SystemRole(Base):
    """
    Represents a platform-wide Role-Based Access Control (RBAC) role.
    """

    __tablename__ = TargetTable.SYSTEM_ROLES.table
    __table_args__ = {"schema": TargetTable.SYSTEM_ROLES.schema}

    code: Mapped[str] = column_short_text(length=50, unique=True)
    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str | None] = column_long_text(nullable=True)

    permission_links: Mapped[list["SystemRolePermissionLink"]] = relationship(
        "SystemRolePermissionLink", back_populates="system_role"
    )
    user_links: Mapped[list["UserSystemRoleLink"]] = relationship(
        "UserSystemRoleLink", back_populates="system_role"
    )


# =====================================================================
# 3. ENTITLEMENTS / TIERS
# =====================================================================


class UserTier(Base):
    """
    Defines operational quotas, limits, and service-level entitlements for users.
    """

    __tablename__ = TargetTable.USER_TIERS.table
    __table_args__ = {"schema": TargetTable.USER_TIERS.schema}

    code: Mapped[str] = column_short_text(50, unique=True)
    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str | None] = column_long_text(nullable=True)
    max_file_size: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    storage_quota: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    max_requests_per_minute: Mapped[int] = column_integer()
    priority_level: Mapped[int] = column_integer()

    updated_at: Mapped[datetime] = column_updated_at()

    users: Mapped[list["User"]] = relationship("User", back_populates="tier")


# =====================================================================
# 4. AUTH & PROFILE MODELS
# =====================================================================


class RefreshSession(Base):
    """
    Tracks active JWT refresh token sessions and device authentication states.
    """

    __tablename__ = TargetTable.REFRESH_SESSIONS.table
    __table_args__ = {"schema": TargetTable.REFRESH_SESSIONS.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", ondelete="CASCADE"
    )

    jti: Mapped[UUID] = column_uuid()
    refresh_hash: Mapped[str] = column_short_text()

    expires_at: Mapped[datetime] = column_datetime()
    is_active: Mapped[bool] = column_bool()

    user: Mapped["User"] = relationship("User", back_populates="refresh_sessions")


class UserDetails(Base):
    """
    Stores private operational, contact, and professional details for a user.
    """

    __tablename__ = TargetTable.USER_DETAILS.table
    __table_args__ = {"schema": TargetTable.USER_DETAILS.schema}

    user_id: Mapped[UUID] = column_fk(
        f"{TargetTable.USERS.fq_name}.id", unique=True, ondelete="CASCADE"
    )
    name: Mapped[str] = column_short_text(length=255, nullable=False)
    phone: Mapped[str | None] = column_short_text(length=50, nullable=True)
    email_pro: Mapped[str] = column_short_text(length=255, unique=True, nullable=False)
    job_title: Mapped[str | None] = column_short_text(length=255, nullable=True)
    area: Mapped[str | None] = column_short_text(length=255, nullable=True)

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", back_populates="details", uselist=False)


class UserProfile(Base):
    """
    Stores public-facing account profile metadata and media associations.
    """

    __tablename__ = TargetTable.USER_PROFILES.table
    __table_args__ = {"schema": TargetTable.USER_PROFILES.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", unique=True, ondelete="CASCADE"
    )

    avatar_attachment_id: Mapped[UUID | None] = column_fk(
        target=f"{TargetTable.ATTACHMENTS.fq_name}.id",
        ondelete="SET NULL",
        nullable=True,
    )

    biography: Mapped[str | None] = column_long_text(nullable=True)

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", back_populates="profile", uselist=False)
    avatar_attachment: Mapped["Attachment | None"] = relationship("Attachment")


class User(Base):
    """
    Core authentication identity and user account model.
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
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    details: Mapped["UserDetails | None"] = relationship(
        "UserDetails",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    tier: Mapped["UserTier"] = relationship("UserTier", back_populates="users")
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        "RefreshSession", back_populates="user", cascade="all, delete-orphan"
    )
    system_role_links: Mapped[list["UserSystemRoleLink"]] = relationship(
        "UserSystemRoleLink", back_populates="user", cascade="all, delete-orphan"
    )
    actor_links: Mapped[list["UserActorLink"]] = relationship(
        "UserActorLink", back_populates="user", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="user", cascade="all, delete-orphan"
    )

    # Activity Relationships
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user"
    )
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")
