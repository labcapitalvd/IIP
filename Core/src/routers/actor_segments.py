from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared_db import get_session
from shared_utils import TokenContext

from handlers.actor_segments import ActorSegmentHandler

from schemas.actor_segments import RequestActorSegment
from schemas.actor_segments import ResponseActorSegment, ResponseActorSegments


router = APIRouter(tags=["Segmentos"], prefix="/segments")


@router.get(
    "/get/one",
    response_model=ResponseActorSegment,
    response_model_exclude_none=True,
    operation_id="get_one_actor_segment",
)
async def get_one_actor_segments(
    query: Annotated[RequestActorSegment, Query()],
    ctx: TokenContext = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """Obtiene un actor_segment"""
    current_user = await ctx.get_current_user()
    return await ActorSegmentHandler(db, current_user).ActorSegmentRead(
        query.id, query.detailed
    )


@router.get(
    "/get/all",
    response_model=ResponseActorSegments,
    response_model_exclude_none=True,
    operation_id="get_all_actor_segments",
)
async def get_all_actor_segments(
    detailed: bool = Query(False, description="Return detailed data"),
    ctx: TokenContext = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """Obtiene todos los actor_segmentes"""
    current_user = await ctx.get_current_user()
    return await ActorSegmentHandler(db, current_user).ActorSegmentReadAll(detailed)
