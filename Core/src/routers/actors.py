from typing import Any, List, Sequence
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path
from shared_schemas import ResponseMessageSchema, ActorSegmentSchema, ActorSchema
from shared_utils import AccessContext, get_claims

from application import IdentityAppService

router = APIRouter(tags=["Submissions"], prefix="/submissions")


def get_identity_service() -> IdentityAppService:
    return IdentityAppService()


@router.get(
    path="/actors",
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


@router.get(
    path="/actors/{actor_id}",
    response_model=ActorSchema,
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

@router.post(
    "/actors/new",
    response_model=ResponseMessageSchema,
    response_model_exclude_none=True,
    operation_id="create_actor",
)
async def create_actor(
    actor: ActorSchema,
    ctx: AccessContext = Depends(),
    service: IdentityAppService = Depends(get_identity_service),
):
    user_id = get_claims(ctx.access_token)
    await service.create_actor(
        data=actor
    )
    return ResponseMessageSchema(message="ok")
