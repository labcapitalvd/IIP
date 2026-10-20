from shared.models import User, UserTier
from shared.utils.hashing import hash_password, verify_password

from ..errors import (
    InvalidCredentials,
    UserAlreadyExists,
    UserTierDoesntExist,
)

DUMMY_HASH = hash_password(password="this-value-does-not-matter")


class UserDomainService:
    """Pure domain logic for user lifecycle rules."""

    @staticmethod
    def register_user(
        username: str,
        email: str,
        password: str,
        existing_user: User | None,
        default_tier: UserTier | None,
    ) -> User:
        if existing_user:
            raise UserAlreadyExists()

        if not default_tier:
            raise UserTierDoesntExist()

        return User(
            tier_id=default_tier.id,
            username=username,
            email=email,
            password_hash=hash_password(password=password),
            is_active=True,
        )

    @staticmethod
    def verify_credentials(user: User | None, password: str) -> User:
        stored_hash = user.password_hash if user else DUMMY_HASH

        try:
            verify_password(password=password, hashed_password=stored_hash)
        except Exception as e:
            raise InvalidCredentials() from e

        if not user:
            raise InvalidCredentials("Invalid credentials")

        return user
