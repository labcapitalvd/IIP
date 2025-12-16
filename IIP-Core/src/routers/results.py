from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared_utils.auth.auth import TokenContext

from handlers.results import ResultHandler

from schemas.results import RequestResult

from shared_db import get_session

router = APIRouter(tags=["Resultados"], prefix="/results")

@router.get(
    "/get/one",
    response_model_exclude_none=True,
    operation_id="get_one_results",
)
async def get_one_form(
    query: Annotated[RequestResult, Query()],
    ctx: TokenContext = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """Obtiene una edición de índice"""
    current_user = await ctx.get_current_user()
    return await ResultHandler(db, current_user).ResultRead(query.id, query.detailed)


@router.get(
    "/get/all",
    response_model_exclude_none=True,
    operation_id="get_all_results",
)
async def get_all_forms(
    detailed: bool = Query(False, description="Return detailed data"),
    ctx: TokenContext = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """Obtiene todas las ediciones de índices"""
    current_user = await ctx.get_current_user()
    return await ResultHandler(db, current_user).ResultReadAll(detailed)
