from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared_utils import TokenContext

from handlers.forms import FormHandler

from schemas.forms import RequestForm
from schemas.forms import ResponseForm, ResponseForms

from shared_db import get_session

router = APIRouter(tags=["Formularios"], prefix="/forms")


@router.get(
    "/get/one",
    response_model=ResponseForm,
    response_model_exclude_none=True,
    operation_id="get_one_form",
)
async def get_one_form(
    query: Annotated[RequestForm, Query()],
    ctx: TokenContext = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """Obtiene una edición de índice"""
    current_user = await ctx.get_current_user()
    return await FormHandler(db, current_user).FormRead(query.id, query.detailed)


@router.get(
    "/get/all",
    response_model=ResponseForms,
    response_model_exclude_none=True,
    operation_id="get_all_forms",
)
async def get_all_forms(
    detailed: bool = Query(False, description="Return detailed data"),
    ctx: TokenContext = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """Obtiene todas las ediciones de índices"""
    current_user = await ctx.get_current_user()
    return await FormHandler(db, current_user).FormReadAll(detailed)
