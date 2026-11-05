from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from application import AuthAppService
from schemas.auth import (
    RequestLogin,
    RequestRegister,
    RequestUpdateUser,
    ResponseMe,
    ResponseUserListItem,
)


from shared.schemas import ResponseAuthSchema, ResponseMessageSchema
from shared.utils import AccessContext, SessionContext, get_claims

router = APIRouter(tags=["Autenticación"], prefix="/auth")


def get_auth_service() -> AuthAppService:
    return AuthAppService()


@router.post(
    "/register",
    response_model=ResponseMessageSchema,
    response_model_exclude_none=True,
    operation_id="register_user",
)
async def register(
        form: RequestRegister,
        service: AuthAppService = Depends(get_auth_service)
        ):
    """Function for registering"""
    await service.register(
        form.username,
        form.email,
        form.password.get_secret_value(),
        actor_id=form.actor_id,
        contact_person=form.contact_person,
        phone=form.phone,
    )
    return ResponseMessageSchema(message="ok")


@router.get(
    "/me",
    response_model=ResponseMe,
    response_model_exclude_none=True,
    operation_id="get_current_user",
)
async def get_me(
    ctx: AccessContext = Depends(),
    service: AuthAppService = Depends(get_auth_service),
):
    """Returns the authenticated user's profile, resolved fresh from the database."""
    claims = get_claims(token=ctx.access_token)
    return await service.get_me(user_id=UUID(claims["sub"]))


@router.post(
    "/login",
    response_model=ResponseAuthSchema,
    response_model_exclude_none=True,
    operation_id="login_user",
)
async def login(
    form_data: RequestLogin,
    ctx: SessionContext = Depends(),
    service: AuthAppService = Depends(get_auth_service)
):
    """Function for logging in"""
    access_token, refresh_token = await service.login(
        username=form_data.username, password=form_data.password.get_secret_value()
    )
    return ctx.make_response(access_token, refresh_token)


@router.post(
    "/reauth",
    response_model=ResponseAuthSchema,
    response_model_exclude_none=True,
    operation_id="reauth_user",
)
async def refresh_token(
    ctx: SessionContext = Depends(),
    service: AuthAppService = Depends(get_auth_service)
):
    """Function for refreshing token"""
    new_access, new_refresh = await service.reauth(
        client_refresh_token=ctx.refresh_token
    )
    return ctx.make_response(new_access, new_refresh)


@router.post(
    "/logout",
    response_model=ResponseMessageSchema,
    response_model_exclude_none=True,
    operation_id="logout_user",
)
async def logout(
    ctx: SessionContext = Depends(),
    service: AuthAppService = Depends(get_auth_service)
):
    """Function for logging out"""
    await service.logout(client_refresh_token=ctx.refresh_token)
    ctx.unset_refresh_cookie()
    return ResponseMessageSchema(message="ok")


@router.get(
    "/users",
    response_model=Sequence[ResponseUserListItem],
    response_model_exclude_none=True,
    operation_id="list_users",
)
async def list_users(
    ctx: AccessContext = Depends(),
    service: AuthAppService = Depends(get_auth_service),
):
    """Lists all user accounts. Administrators only (403 otherwise)."""
    claims = get_claims(token=ctx.access_token)
    return await service.list_users(requester_id=UUID(claims["sub"]))


@router.put(
    "/users/{user_id}",
    response_model=ResponseMessageSchema,
    response_model_exclude_none=True,
    operation_id="update_user",
)
async def update_user(
    body: RequestUpdateUser,
    user_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: AuthAppService = Depends(get_auth_service),
):
    """Activates/deactivates a user or edits contact data. Administrators only."""
    claims = get_claims(token=ctx.access_token)
    await service.update_user(UUID(claims["sub"]), user_id, body)
    return ResponseMessageSchema(message="ok")


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_user",
)
async def delete_user(
    user_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: AuthAppService = Depends(get_auth_service),
):
    """Deletes a user account. Administrators only; admins cannot delete themselves."""
    claims = get_claims(token=ctx.access_token)
    await service.delete_user(UUID(claims["sub"]), user_id)
