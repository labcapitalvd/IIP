from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from domain import ActorService
from infrastructure.uow import IdentityUoW

from shared_models import Actor, ActorSegment
from shared_schemas import ActorSchema, ActorSegmentSchema

class IdentityAppService:
    def __init__(
        self,
        actor_service: ActorService | None = None,
    ):
        self.actor_service = actor_service or ActorService()

    async def create_actor(self, data: ActorSchema) -> ActorSchema:
        async with IdentityUoW() as uow:
            a: Actor = await self.actor_service.create_actor(
                uow=uow, actor_data=data
            )
            return ActorSchema(
                id=a.id,
                label=a.label,
                description=a.description,
                actor_segment=a.actor_segment.label,
                mission=a.mission,
                vision=a.vision
            )

    async def get_all_actors(self) -> Sequence[ActorSchema]:
        async with IdentityUoW() as uow:
            actors: Sequence[Actor] = await uow.actors.get_all()
            
            return [
                ActorSchema(
                    id=a.id,
                    label=a.label,
                    description=a.description,
                    actor_segment=a.actor_segment.label,
                    mission=a.mission,
                    vision=a.vision
                ) for a in actors
            ]

    async def get_one_actor(self, id: UUID) -> ActorSchema:
        async with IdentityUoW() as uow:
            a: Actor = await uow.actors.get_by_id(id=id)
            
            return ActorSchema(
                id=a.id,
                label=a.label,
                description=a.description,
                actor_segment=a.actor_segment.label,
                mission=a.mission,
                vision=a.vision
            )


