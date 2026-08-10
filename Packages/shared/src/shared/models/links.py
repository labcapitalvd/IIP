from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, relationship

from shared.db import Base, column_fk, column_updated_at

from .targets import TargetTable

if TYPE_CHECKING:
    from .actors import Actor
    from .auth import Permission, ResourceRole, SystemRole, User
    from .forms import FieldChoice
    from .submissions import AnswerMultiChoice


class SystemRolePermissionLink(Base):
    """
    Join table mapping global platform permissions to global `SystemRole` models (RBAC).
    """

    __tablename__ = TargetTable.LINK_SYSTEM_ROLE_PERMISSION.table
    __table_args__ = {"schema": TargetTable.LINK_SYSTEM_ROLE_PERMISSION.schema}

    system_role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SYSTEM_ROLES.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    permission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.PERMISSIONS.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    system_role: Mapped["SystemRole"] = relationship(
        "SystemRole", back_populates="permission_links"
    )
    permission: Mapped["Permission"] = relationship(
        "Permission", back_populates="system_role_links"
    )


class ResourceRolePermissionLink(Base):
    """
    Join table mapping granular permissions to scoped `ResourceRole` models (ReBAC).

    Defines capabilities enabled for a scoped resource role (e.g., 'evaluator' or 'reviewer').
    When a user is assigned a `ResourceRole` within an `Actor` context (via `UserActorLink`),
    these mapped permissions dictate what actions they can perform inside that context.
    """

    __tablename__ = TargetTable.LINK_RESOURCE_ROLE_PERMISSION.table
    __table_args__ = {"schema": TargetTable.LINK_RESOURCE_ROLE_PERMISSION.schema}

    resource_role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.RESOURCE_ROLES.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    permission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.PERMISSIONS.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    resource_role: Mapped["ResourceRole"] = relationship(
        "ResourceRole", back_populates="permission_links"
    )
    permission: Mapped["Permission"] = relationship(
        "Permission", back_populates="resource_role_links"
    )


class UserSystemRoleLink(Base):
    """
    Join table assigning global `SystemRole` instances directly to `User` accounts.
    """

    __tablename__ = TargetTable.LINK_USER_SYSTEM_ROLE.table
    __table_args__ = {"schema": TargetTable.LINK_USER_SYSTEM_ROLE.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    system_role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SYSTEM_ROLES.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", back_populates="system_role_links")
    system_role: Mapped["SystemRole"] = relationship(
        "SystemRole", back_populates="user_links"
    )


class UserActorLink(Base):
    """
    Primary Relationship-Based Access Control (ReBAC) join table connecting users to actors.

    Establishes tenant/entity membership by linking a `User` to an `Actor` (Organization,
    Workspace, Team, Department) and specifying their context-scoped `ResourceRole`.
    """

    __tablename__ = TargetTable.LINK_USER_ACTOR.table
    __table_args__ = {"schema": TargetTable.LINK_USER_ACTOR.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    actor_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTORS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    resource_role_id: Mapped[UUID | None] = column_fk(
        target=f"{TargetTable.RESOURCE_ROLES.fq_name}.id",
        nullable=True,
        ondelete="CASCADE",
    )

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", back_populates="actor_links")
    actor: Mapped["Actor"] = relationship("Actor", back_populates="user_links")
    resource_role: Mapped["ResourceRole | None"] = relationship(
        "ResourceRole", back_populates="actor_links"
    )


class MultiChoiceOptionLink(Base):
    """
    Join table connecting selected `FieldChoice` options to a multi-choice answer submission.
    """

    __tablename__ = TargetTable.LINK_CHOICE_MULTICHOICE.table
    __table_args__ = {"schema": TargetTable.LINK_CHOICE_MULTICHOICE.schema}

    choice_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELD_CHOICES.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    multi_choice_answer_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS_MULTI_CHOICE.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    updated_at: Mapped[datetime] = column_updated_at()

    choice: Mapped["FieldChoice"] = relationship(
        "FieldChoice", back_populates="answer_links"
    )
    answer: Mapped["AnswerMultiChoice"] = relationship(
        "AnswerMultiChoice", back_populates="option_links"
    )
