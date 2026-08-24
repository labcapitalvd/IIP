from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from services.domain import PermissionCompiler, TokenDomainService, UserDomainService
from services.domain import (
    InvalidCredentials,
    TokenMalformed,
    UserInactive,
)
from shared.models import RefreshSession, User
from shared.utils.hashing import hash_token, verify_token
from shared.utils.logger import getLogger
from shared.utils.tokens import decode_token, generate_token

from infrastructure.uow import AuthUoW

logger = getLogger(__name__)


class AuthAppService:
    """Application orchestrator managing transactions, DB access, and side effects."""

    async def register(self, username: str, email: str, password: str) -> User:
        async with AuthUoW() as uow:
            existing_user = await uow.users.get_by_username(username)
            default_tier = await uow.tiers.get_default()

            user = UserDomainService.register_user(
                username=username,
                email=email,
                password=password,
                existing_user=existing_user,
                default_tier=default_tier,
            )

            uow.users.add(user)
            return user

    async def login(self, username: str, password: str) -> tuple[str, str]:
        async with AuthUoW() as uow:
            user = await uow.users.get_by_username(username)
            user = UserDomainService.verify_credentials(user=user, password=password)

            return await self._issue_tokens_internal(
                user_id=user.id, username=user.username, uow=uow
            )

    async def reauth(self, client_refresh_token: str) -> tuple[str, str]:
        async with AuthUoW() as uow:
            db_token, decoded = await self._verify_and_deactivate_session(
                client_refresh_token=client_refresh_token, uow=uow
            )

            # Defensive narrowing for static analyzers when ignore_missing is False
            assert db_token is not None

            return await self._issue_tokens_internal(
                user_id=db_token.user_id,
                username=decoded["username"],
                uow=uow,
            )

    async def logout(self, client_refresh_token: str) -> None:
        async with AuthUoW() as uow:
            await self._verify_and_deactivate_session(
                client_refresh_token=client_refresh_token,
                uow=uow,
                ignore_missing=True,
            )

    async def delete_account(self, username: str, password: str) -> User:
        async with AuthUoW() as uow:
            user = await uow.users.get_by_username(username)
            user = UserDomainService.verify_credentials(user=user, password=password)

            await uow.users.delete(user)
            return user

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    async def _verify_and_deactivate_session(
        self, client_refresh_token: str, uow: AuthUoW, ignore_missing: bool = False
    ) -> tuple[RefreshSession | None, dict[str, Any]]:
        """Extracts, verifies, and revokes a refresh session atomically within a UoW context."""
        try:
            dec = decode_token(token=client_refresh_token, expected_type="refresh")
            decoded = dec.claims
            jti = UUID(str(decoded["jti"]))
            user_id = UUID(str(decoded["sub"]))
        except Exception as e:
            logger.warning("Invalid refresh token payload: %s", e)
            raise TokenMalformed() from e

        raw_session = await uow.tokens.get_by_jti(user_id=user_id, jti=jti)

        if raw_session is None and ignore_missing:
            return None, decoded

        # Domain validation: raises TokenRevoked or TokenExpired if invalid
        db_token = TokenDomainService.validate_refresh_session(
            session=raw_session, current_time=datetime.now(timezone.utc)
        )

        # Cryptographic verification
        try:
            verify_token(token=client_refresh_token, hashed_token=db_token.refresh_hash)
        except Exception as e:
            logger.warning("Cryptographic hash mismatch for jti=%s: %s", jti, e)
            raise InvalidCredentials() from e

        # Deactivate session & queue Valkey cache purge
        await uow.tokens.deactivate(user_id=user_id, jti=jti)
        uow.invalidate_session_cache(jti=str(jti))

        return db_token, decoded

    async def _issue_tokens_internal(
        self, user_id: UUID, username: str, uow: AuthUoW
    ) -> tuple[str, str]:
        """Generates JWTs, persists session tracking model, and schedules cache sync."""
        client_access_token, _, _ = generate_token(
            user_id=user_id, username=username, token_type="access"
        )
        client_refresh_token, expr, jti = generate_token(
            user_id=user_id, username=username, token_type="refresh"
        )
        assert jti is not None, "Refresh token must have a JTI"

        user_context = await uow.users.get_with_auth_context(user_id)
        if not user_context or not user_context.is_active:
            raise UserInactive()

        parsed_jti = UUID(jti) if isinstance(jti, str) else jti

        db_token = RefreshSession(
            jti=parsed_jti,
            user_id=user_id,
            refresh_hash=hash_token(token=client_refresh_token),
            is_active=True,
            expires_at=datetime.fromtimestamp(expr, tz=timezone.utc),
        )
        uow.tokens.add(db_token)

        permission_map = PermissionCompiler.compile(user_context)
        ttl = max(0, expr - int(datetime.now(timezone.utc).timestamp()))

        uow.schedule_session_cache_sync(
            jti=str(parsed_jti), permission_map=permission_map, ttl_seconds=ttl
        )

        return client_access_token, client_refresh_token
