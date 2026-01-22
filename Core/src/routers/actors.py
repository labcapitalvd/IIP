from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared_db import get_session
from shared_utils import TokenContext

from handlers.actors import ActorHandler

from schemas.actors import RequestActor
from schemas.actors import ResponseActor, ResponseActors


router = APIRouter(tags=["Actores"], prefix="/actors")


@router.get(
    "/get/one",
    response_model=ResponseActor,
    response_model_exclude_none=True,
    operation_id="get_one_actor",
)
async def get_one_actor(
    query: Annotated[RequestActor, Query()],
    ctx: TokenContext = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """Obtiene una entidad por su ID"""
    current_user = await ctx.get_current_user()
    return await ActorHandler(db, current_user).ActorRead(query.id, query.detailed)


@router.get(
    "/get/all",
    response_model=ResponseActors,
    response_model_exclude_none=True,
    operation_id="get_all_actors",
)
async def get_all_actors(
    detailed: bool = Query(False, description="Return detailed data"),
    ctx: TokenContext = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """Obtiene todas las entidades"""
    current_user = await ctx.get_current_user()
    return await ActorHandler(db, current_user).ActorReadAll(detailed)
