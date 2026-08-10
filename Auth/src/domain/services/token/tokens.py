from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from shared.models import RefreshSession
from shared.utils import get_logger
from shared.utils.hashing import hash_token, verify_token
from shared.utils.tokens import decode_token, generate_token

from infrastructure.uow import AuthUoW

from .errors import TokenError, TokenExpired, TokenRevoked

logger = get_logger(__name__)

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


class TokenService:
    async def issue_tokens(
        self, user_id: UUID, username: str, uow: AuthUoW
    ) -> tuple[str, str]:
        """Generate access and refresh tokens and cache user session permissions."""
        client_access_token, _, _ = generate_token(
            user_id=user_id, username=username, token_type="access"
        )
        client_refresh_token, expr, jti = generate_token(
            user_id=user_id, username=username, token_type="refresh"
        )
        assert jti is not None, "Refresh token must have a JTI"

        # 1. Fetch user entity graph eagerly with auth context
        user = await uow.users.get_with_auth_context(user_id)
        if not user or not user.is_active:
            raise TokenError("User is inactive or not found.")

        # 2. Add refresh session DB model
        refresh_hash = hash_token(token=client_refresh_token)
        db_token = RefreshSession(
            jti=jti,
            user_id=user_id,
            refresh_hash=refresh_hash,
            is_active=True,
            expires_at=datetime.fromtimestamp(expr, tz=timezone.utc),
        )
        uow.tokens.add(db_token)

        # 3. Compile permissions & schedule Valkey write hook
        permission_map = PermissionCompiler.compile(user)
        ttl = max(0, expr - int(datetime.now(timezone.utc).timestamp()))

        uow.schedule_session_cache_sync(
            jti=jti,
            permission_map=permission_map,
            ttl_seconds=ttl,
        )

        return client_access_token, client_refresh_token

    async def reauth(self, client_refresh_token: str, uow: AuthUoW) -> tuple[str, str]:
        """Invalidate old refresh token and issue new tokens."""
        dec = decode_token(token=client_refresh_token, expected_type="refresh")
        decoded = dec.claims
        jti = decoded["jti"]
        user_id = decoded["sub"]
        username = decoded["username"]

        db_token = await uow.tokens.get_by_jti(user_id=user_id, jti=jti)
        if db_token is None or not db_token.is_active:
            logger.warning(
                "Attempt to use revoked refresh token on reauth: jti=%s", jti
            )
            raise TokenRevoked()

        if db_token.expires_at < datetime.now(timezone.utc):
            raise TokenExpired()

        try:
            verify_token(token=client_refresh_token, hashed_token=db_token.refresh_hash)
        except Exception as e:
            logger.warning(
                "Failed to verify refresh token on reauth: jti=%s, reason=%s", jti, e
            )
            raise TokenError() from e

        await uow.tokens.deactivate(user_id=user_id, jti=jti)
        uow.invalidate_session_cache(jti=jti)

        return await self.issue_tokens(user_id=user_id, username=username, uow=uow)

    async def logout(self, client_refresh_token: str, uow: AuthUoW) -> None:
        """Invalidate refresh token and purge session permissions from cache."""
        dec = decode_token(token=client_refresh_token, expected_type="refresh")
        decoded = dec.claims
        jti = decoded["jti"]
        user_id = decoded["sub"]

        db_token = await uow.tokens.get_by_jti(user_id=user_id, jti=jti)
        if db_token is None:
            logger.warning(
                "Attempt to use revoked refresh token on logout: jti=%s", jti
            )
            return

        try:
            verify_token(token=client_refresh_token, hashed_token=db_token.refresh_hash)
        except Exception as e:
            logger.warning(
                "Failed to verify refresh token on logout: jti=%s, reason=%s", jti, e
            )
            raise TokenError() from e

        await uow.tokens.deactivate(user_id=user_id, jti=jti)
        uow.invalidate_session_cache(jti=jti)
