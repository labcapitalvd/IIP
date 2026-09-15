from uuid import UUID

from shared.enums import SystemRolesEnum
from shared.models import User, UserActorLink, UserDetails, UserSystemRoleLink
from shared.utils.hashing import hash_password, verify_password

from infrastructure.uow import AuthUoW

from .errors import (
    ActorNotFoundError,
    DefaultRoleDoesntExist,
    InvalidCredentials,
    TierDoesntExist,
    UserAlreadyExists,
)


DUMMY_HASH = hash_password(password="this-value-does-not-matter")


class AuthService:
    async def register(
        self,
        username: str,
        email: str,
        password: str,
        uow: AuthUoW,
        actor_id: str | None = None,
        contact_person: str | None = None,
        phone: str | None = None,
    ) -> User:
        """Register user."""
        if await uow.users.get_by_username(username):
            raise UserAlreadyExists()

        if await uow.users.get_by_email(email):
            raise UserAlreadyExists("A user with this email already exists.")

        default_tier = await uow.tiers.get_default()
        if not default_tier:
            raise TierDoesntExist()

        default_role = await uow.system_roles.get_by_code(
            SystemRolesEnum.STANDARD_USER.code
        )
        if not default_role:
            raise DefaultRoleDoesntExist()

        password_hash = hash_password(password=password)

        user = User(
            tier_id=default_tier.id,
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=True,
        )

        # Every account gets the platform-wide "standard_user" role so it can
        # be told apart from privileged accounts (which are provisioned
        # separately, never through public self-registration).
        user.system_role_links.append(UserSystemRoleLink(system_role=default_role))

        # Optional entity membership (ReBAC): links the new account to the
        # Actor (distrital entity) it represents, if one was selected.
        if actor_id:
            actor = await uow.actors.get_by_id(id=UUID(actor_id))
            if not actor:
                raise ActorNotFoundError()
            user.actor_links.append(UserActorLink(actor=actor))

        # Optional contact profile — only created when actually provided, so
        # UserDetails' NOT NULL columns are never touched with empty data.
        if contact_person:
            user.details = UserDetails(
                name=contact_person,
                phone=phone,
                email_pro=email,
            )

        uow.users.add(user)
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

        await uow.users.delete(user)
        return user
