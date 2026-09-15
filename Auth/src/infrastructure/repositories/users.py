from uuid import UUID

from shared.db import BaseRepository
from shared.models import (
    Actor,
    ResourceRole,
    ResourceRolePermissionLink,
    SystemRole,
    SystemRolePermissionLink,
    User,
    UserActorLink,
    UserSystemRoleLink,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class UserRepository(BaseRepository[User]):
    """Handles pure DB operations for User entities."""

    model = User

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_auth_context(self, id: UUID) -> User | None:
        """Fetch user with fully eagerly loaded RBAC, ReBAC, Tier and profile models."""
        stmt = (
            select(User)
            .where(User.id == id)
            .options(
                selectinload(User.tier),
                selectinload(User.details),
                selectinload(User.profile),
                # Global RBAC
                selectinload(User.system_role_links)
                .selectinload(UserSystemRoleLink.system_role)
                .selectinload(SystemRole.permission_links)
                .selectinload(SystemRolePermissionLink.permission),
                # Scoped ReBAC
                selectinload(User.actor_links).selectinload(UserActorLink.actor),
                selectinload(User.actor_links)
                .selectinload(UserActorLink.resource_role)
                .selectinload(ResourceRole.permission_links)
                .selectinload(ResourceRolePermissionLink.permission),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SystemRoleRepository(BaseRepository[SystemRole]):
    """Handles DB operations for SystemRole (RBAC)."""

    model = SystemRole

    async def get_by_code(self, code: str) -> SystemRole | None:
        stmt = select(SystemRole).where(SystemRole.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ResourceRoleRepository(BaseRepository[ResourceRole]):
    """Handles DB operations for ResourceRole (ReBAC)."""

    model = ResourceRole


class ActorRepository(BaseRepository[Actor]):
    """Read-only access to Actor from the Auth service, used to validate and
    link a newly registered user to an entity (UserActorLink)."""

    model = Actor
