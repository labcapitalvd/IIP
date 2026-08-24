from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from shared.models import RefreshSession, User
from shared.utils import getLogger

from ..errors import TokenExpired, TokenRevoked

logger = getLogger(__name__)

if TYPE_CHECKING:
    from shared.models import User


class PermissionCompiler:
    """Transforms a User entity graph into a flat string mapping for Valkey hash storage."""

    @staticmethod
    def compile(user: User) -> dict[str, str]:
        # 1. Base User State
        permission_map: dict[str, str] = {
            "user_id": str(user.id),
            "is_active": str(user.is_active).lower(),
        }

        # 2. ABAC Attributes (Tier Limits)
        if user.tier:
            permission_map.update(
                {
                    "tier": str(user.tier.label),
                    "max_file_size": str(user.tier.max_file_size),
                    "storage_quota": str(user.tier.storage_quota),
                    "max_requests_per_minute": str(user.tier.max_requests_per_minute),
                    "priority_level": str(user.tier.priority_level),
                }
            )

        # 3. Global RBAC
        global_roles: list[str] = []
        global_permissions: set[str] = set()

        for s_link in user.system_role_links:
            if s_link.system_role:
                global_roles.append(s_link.system_role.code)
                for p_link in s_link.system_role.permission_links:
                    if p_link.permission:
                        global_permissions.add(p_link.permission.key)

        permission_map["system_roles"] = json.dumps(global_roles)
        permission_map["global_permissions"] = json.dumps(list(global_permissions))

        # 4. Scoped ReBAC
        actor_permissions: dict[str, dict[str, Any]] = {}

        for a_link in user.actor_links:
            actor_id_str = str(a_link.actor_id)
            resource_role_code = (
                a_link.resource_role.code if a_link.resource_role else "member"
            )

            scoped_perms: list[str] = []
            if a_link.resource_role:
                for p_link in a_link.resource_role.permission_links:
                    if p_link.permission:
                        scoped_perms.append(p_link.permission.key)

            actor_permissions[actor_id_str] = {
                "resource_role": resource_role_code,
                "permissions": scoped_perms,
            }

        permission_map["actor_permissions"] = json.dumps(actor_permissions)

        return permission_map


class TokenDomainService:
    """Pure domain logic for session invariants."""

    @staticmethod
    def validate_refresh_session(
        session: RefreshSession | None, current_time: datetime
    ) -> RefreshSession:
        if session is None or not session.is_active:
            raise TokenRevoked()

        if session.expires_at < current_time:
            raise TokenExpired()

        return session
