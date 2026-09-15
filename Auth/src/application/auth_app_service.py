from uuid import UUID

from domain import AuthService, TokenService
from domain.services.auth.errors import UserNotFound
from infrastructure.uow import AuthUoW

from shared.models import User
from schemas.auth import ResponseMe, ResponseMeActorLink


class AuthAppService:
    def __init__(
        self,
        auth_service: AuthService | None = None,
        token_service: TokenService | None = None,
    ):
        self.auth_service = auth_service or AuthService()
        self.token_service = token_service or TokenService()

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        actor_id: str | None = None,
        contact_person: str | None = None,
        phone: str | None = None,
    ) -> User:
        async with AuthUoW() as uow:
            return await self.auth_service.register(
                username=username,
                email=email,
                password=password,
                uow=uow,
                actor_id=actor_id,
                contact_person=contact_person,
                phone=phone,
            )

    async def login(self, username: str, password: str) -> tuple[str, str]:
        async with AuthUoW() as uow:
            user = await self.auth_service.login(
                username=username, password=password, uow=uow
            )
            tokens = await self.token_service.issue_tokens(
                user_id=user.id, username=user.username, uow=uow
            )
            return tokens

    async def reauth(self, client_refresh_token: str) -> tuple[str, str]:
        async with AuthUoW() as uow:
            return await self.token_service.reauth(
                client_refresh_token=client_refresh_token, uow=uow
            )

    async def logout(self, client_refresh_token: str) -> None:
        async with AuthUoW() as uow:
            await self.token_service.logout(
                client_refresh_token=client_refresh_token, uow=uow
            )

    async def get_me(self, user_id: UUID) -> ResponseMe:
        """
        Builds the authenticated user's profile straight from the database —
        this is the single source of truth the frontend should hydrate from
        instead of caching profile data locally.
        """
        async with AuthUoW() as uow:
            user = await uow.users.get_with_auth_context(user_id)
            if not user:
                raise UserNotFound()

            return ResponseMe(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                tier=user.tier.code if user.tier else None,
                system_roles=[
                    link.system_role.code
                    for link in user.system_role_links
                    if link.system_role
                ],
                actor_links=[
                    ResponseMeActorLink(
                        actor_id=link.actor_id,
                        actor_label=link.actor.label if link.actor else "",
                        resource_role=link.resource_role.code
                        if link.resource_role
                        else None,
                    )
                    for link in user.actor_links
                ],
                name=user.details.name if user.details else None,
                phone=user.details.phone if user.details else None,
            )
