from uuid import UUID

from shared.db import UnitOfWork
from shared.infrastructure import valkey_client

from ..repositories import (
    RefreshTokenRepository,
    RoleRepository,
    TierRepository,
    UserRepository,
)


class AuthUoW(UnitOfWork):
    users: UserRepository
    roles: RoleRepository
    tiers: TierRepository
    tokens: RefreshTokenRepository

    def _init_repositories(self) -> None:
        assert self.session is not None
        self.users = UserRepository(self.session)
        self.roles = RoleRepository(self.session)
        self.tiers = TierRepository(self.session)
        self.tokens = RefreshTokenRepository(self.session)

    async def sync_session_cache(
        self, user_id: UUID, jti: UUID, ttl_seconds: int = 3600
    ) -> bool:
        """Asks the repository for data and schedules the post-commit Valkey dump."""
        # 1. Ask the repository to do the heavy pulling and mapping lifting
        permission_map = await self.users.compile_permission_map(user_id)
        if not permission_map:
            return False

        # 2. Package the networking operation into the hook
        async def valkey_write_operation() -> None:
            cache_key = f"session:{jti}:permissions"
            async with valkey_client.pipeline(transaction=True) as pipe:
                pipe.hset(cache_key, mapping=permission_map)
                pipe.expire(cache_key, ttl_seconds)
                await pipe.execute()

        # 3. Schedule execution strictly after PostgreSQL successfully writes
        self.add_post_commit_hook(valkey_write_operation)
        return True

    def invalidate_session_cache(self, jti: UUID) -> None:
        """Schedule session deletion from Valkey post-commit."""

        async def valkey_delete_operation() -> None:
            cache_key = f"session:{jti}:permissions"
            await valkey_client.delete(cache_key)

        self.add_post_commit_hook(valkey_delete_operation)
