from shared.db import UnitOfWork

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
