from typing import Any, List, Sequence
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path
from shared_schemas import ResponseMessageSchema, ActorSegmentSchema, ActorSchema, ActorSchemaRel, ActorSegmentSchemaRel
from shared_utils import AccessContext, get_claims

from application import IdentityAppService


router_actors = APIRouter(tags=["Actors"], prefix="/actors")
router_actor_segments = APIRouter(tags=["Actors"], prefix="/actor_segments")


def get_identity_service() -> IdentityAppService:
    return IdentityAppService()


@router_actors.get(
    path="/all",
    response_model=Sequence[ActorSchema],
    response_model_exclude_none=True,
    operation_id="get_entities",
)
async def get_actors(
    ctx: AccessContext = Depends(),
    service: IdentityAppService = Depends(dependency=get_identity_service),
):
    user_id = get_claims(token=ctx.access_token)
    response = await service.get_all_actors()
    return response


@router_actors.get(
    path="/{actor_id}",
    response_model=ActorSchemaRel,
    response_model_exclude_none=True,
    operation_id="get_entity",
)
async def get_actor(
    actor_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: IdentityAppService = Depends(dependency=get_identity_service),
):
    user_id = get_claims(token=ctx.access_token)
    response = await service.get_one_actor(id=actor_id)
    return response


@router_actors.post(
    "/new",
    response_model=ResponseMessageSchema,
    response_model_exclude_none=True,
    operation_id="create_actor",
)
async def create_actor(
    actor: ActorSchemaRel,
    ctx: AccessContext = Depends(),
    service: IdentityAppService = Depends(get_identity_service),
):
    user_id = get_claims(ctx.access_token)
    await service.create_actor(data=actor)
    return ResponseMessageSchema(message="ok")



@router_actor_segments.get(
    path="/all",
    response_model=Sequence[ActorSegmentSchema],
    response_model_exclude_none=True,
    operation_id="get_actor_segments",
)
async def get_actor_segments(
    ctx: AccessContext = Depends(),
    service: IdentityAppService = Depends(dependency=get_identity_service),
):
    user_id = get_claims(token=ctx.access_token)
    response = await service.get_all_actor_segments()
    return response


@router_actor_segments.get(
    path="/{actor_segment_id}",
    response_model=ActorSegmentSchemaRel,
    response_model_exclude_none=True,
    operation_id="get_actor_segment",
)
async def get_actor_segment(
    actor_segment_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: IdentityAppService = Depends(dependency=get_identity_service),
):
    user_id = get_claims(token=ctx.access_token)
    response = await service.get_one_actor_segment(id=actor_segment_id)
    return response


@router_actor_segments.post(
    "/new",
    response_model=ResponseMessageSchema,
    response_model_exclude_none=True,
    operation_id="create_actor_segment",
)
async def create_actor_segment(
    actor_segment: ActorSegmentSchema,
    ctx: AccessContext = Depends(),
    service: IdentityAppService = Depends(get_identity_service),
):
    user_id = get_claims(ctx.access_token)
    await service.create_actor_segment(data=actor_segment)
    return ResponseMessageSchema(message="ok")
