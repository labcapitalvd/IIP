from shared_db import UnitOfWork

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

    async def __aenter__(self):
        await super().__aenter__()
        assert self.session is not None

        self.users = UserRepository(self.session)
        self.roles = RoleRepository(self.session)
        self.tiers = TierRepository(self.session)
        self.tokens = RefreshTokenRepository(self.session)

        return self
