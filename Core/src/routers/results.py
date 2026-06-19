from typing import Annotated

from fastapi import APIRouter, Depends, Query

from shared.utils import AccessContext

from schemas.results import RequestResult


router = APIRouter(tags=["Resultados"], prefix="/results")


@router.get(
    "/get/one",
    response_model_exclude_none=True,
    operation_id="get_one_results",
)
async def get_one_form(
    query: Annotated[RequestResult, Query()],
    ctx: AccessContext = Depends(),
):
    """Obtiene una edición de índice"""
