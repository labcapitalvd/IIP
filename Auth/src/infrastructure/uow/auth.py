from uuid import UUID

from shared.db import UnitOfWork
from shared.infrastructure import valkey_client

from ..repositories import (
    RefreshTokenRepository,
    ResourceRoleRepository,
    SystemRoleRepository,
    TierRepository,
    UserRepository,
)


class AuthUoW(UnitOfWork):
    users: UserRepository
    system_roles: SystemRoleRepository
    resource_roles: ResourceRoleRepository
    tiers: TierRepository
    tokens: RefreshTokenRepository

    def _init_repositories(self) -> None:
        if self.session is None:
            raise RuntimeError(
                "Session is not initialized. Ensure UnitOfWork is used within an 'async with' block."
            )

        self.users = UserRepository(self.session)
        self.system_roles = SystemRoleRepository(self.session)
        self.resource_roles = ResourceRoleRepository(self.session)
        self.tiers = TierRepository(self.session)
        self.tokens = RefreshTokenRepository(self.session)

    def schedule_session_cache_sync(
        self, jti: UUID, permission_map: dict[str, str], ttl_seconds: int = 3600
    ) -> None:
        """Schedules Valkey dump hook post-commit."""

        async def valkey_write_operation() -> None:
            cache_key = f"session:{jti}:permissions"
            async with valkey_client.pipeline(transaction=True) as pipe:
                pipe.hset(cache_key, mapping=permission_map)
                pipe.expire(cache_key, ttl_seconds)
                await pipe.execute()

        self.add_post_commit_hook(valkey_write_operation)

    def invalidate_session_cache(self, jti: UUID) -> None:
        """Schedule session deletion from Valkey post-commit."""

        async def valkey_delete_operation() -> None:
            cache_key = f"session:{jti}:permissions"
            await valkey_client.delete(cache_key)

        self.add_post_commit_hook(valkey_delete_operation)
