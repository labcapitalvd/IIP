from shared_utils.hashing import hash_password, verify_password
from shared_models import User

from infrastructure.uow import AuthUoW

from .errors import InvalidCredentials, UserAlreadyExists, TierDoesntExist


DUMMY_HASH = hash_password(password="this-value-does-not-matter")


class AuthService:
    async def register(
        self,
        username: str,
        email: str,
        password: str,
        uow: AuthUoW,
    ) -> User:
        """Register user."""
        if await uow.users.get_by_username(username):
            raise UserAlreadyExists()

        default_tier = await uow.tiers.get_default()
        if not default_tier:
            raise TierDoesntExist()

        password_hash = hash_password(password=password)

        user = User(
            tier_id=default_tier.id,
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=True,
        )

        uow.users.add_user(user)
        return user

    async def login(
        self,
        username: str,
        password: str,
        uow: AuthUoW,
    ) -> User:
        """Login user."""
        user = await uow.users.get_by_username(username)
        stored_hash = user.password_hash if user else DUMMY_HASH
        
        try:
            verify_password(password=password, hashed_password=stored_hash)
        except Exception as e:
            raise InvalidCredentials() from e

        if not user:
            raise InvalidCredentials("Invalid credentials")

        return user

    async def delete_account(
        self,
        username: str,
        password: str,
        uow: AuthUoW,
    ) -> User:
        """Delete user."""
        user = await uow.users.get_by_username(username)
        stored_hash = user.password_hash if user else DUMMY_HASH
        
        try:
            verify_password(password=password, hashed_password=stored_hash)
        except Exception as e:
            raise InvalidCredentials() from e

        if not user:
            raise InvalidCredentials("Invalid credentials")

        uow.users.delete_user(user)
        return user
