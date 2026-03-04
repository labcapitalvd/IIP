from fastapi import APIRouter, Depends, HTTPException

from application import AuthAppService
from schemas.auth import RequestRegister, RequestLogin

from domain.services.auth.errors import UserAlreadyExists

from shared_schemas import ResponseAuth, ResponseMessage
from shared_utils import AccessContext, SessionContext

router = APIRouter(tags=["Autenticación"], prefix="/auth")


@router.post(
    "/register",
    response_model=ResponseMessage,
    response_model_exclude_none=True,
    operation_id="register_user",
)
async def register(form: RequestRegister):
    """Function for registering"""
    await AuthAppService().register(
        form.username,
        form.email,
        form.password.get_secret_value(),
    )
    return ResponseMessage(message="ok")



@router.post(
    "/login",
    response_model=ResponseAuth,
    response_model_exclude_none=True,
    operation_id="login_user",
)
async def login(
    form_data: RequestLogin,
    ctx: SessionContext = Depends(),
):
    """Function for logging in"""
    access_token, refresh_token = await AuthAppService().login(
        username=form_data.username, password=form_data.password.get_secret_value()
    )
    return ctx.make_response(access_token, refresh_token)


@router.post(
    "/reauth",
    response_model=ResponseAuth,
    response_model_exclude_none=True,
    operation_id="reauth_user",
)
async def refresh_token(
    ctx: SessionContext = Depends(),
):
    """Function for refreshing token"""
    new_access, new_refresh = await AuthAppService().reauth(
        client_refresh_token=ctx.refresh_token
    )
    return ctx.make_response(new_access, new_refresh)


@router.post(
    "/logout",
    response_model=ResponseMessage,
    response_model_exclude_none=True,
    operation_id="logout_user",
)
async def logout(
    ctx: SessionContext = Depends(),
):
    """Function for logging out"""
    await AuthAppService().logout(client_refresh_token=ctx.refresh_token)
    ctx.unset_refresh_cookie()
    return ResponseMessage(message="ok")
