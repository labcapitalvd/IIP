from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from domain import ActorService
from infrastructure.uow import IdentityUoW

from shared_models import Actor, ActorSegment
from shared_schemas import (
    ActorSchema,
    ActorSegmentSchema,
    ActorSchemaRel,
    ActorSegmentSchemaRel,
)


class IdentityAppService:
    def __init__(
        self,
        actor_service: ActorService | None = None,
    ):
        self.actor_service = actor_service or ActorService()

    async def create_actor(self, data: ActorSchemaRel) -> ActorSchemaRel:
        async with IdentityUoW() as uow:
            a: Actor = await self.actor_service.create_actor(uow=uow, actor_data=data)
            return ActorSchemaRel(
                id=a.id,
                label=a.label,
                description=a.description,
                mission=a.mission,
                vision=a.vision,
                actor_segment=ActorSegmentSchema(
                    label=a.actor_segment.label, description=a.actor_segment.description
                ),
            )

    async def get_all_actors(self) -> Sequence[ActorSchema]:
        async with IdentityUoW() as uow:
            actors: Sequence[Actor] = await uow.actors.get_all()

            return [
                ActorSchema(
                    id=a.id,
                    label=a.label,
                    description=a.description,
                    mission=a.mission,
                    vision=a.vision,
                )
                for a in actors
            ]

    async def get_one_actor(self, id: UUID) -> ActorSchemaRel:
        async with IdentityUoW() as uow:
            a: ActorSegment = await uow.actors.get_by_id(id=id)

            return ActorSchemaRel(
                id=a.id,
                label=a.label,
                description=a.description,
                mission=a.mission,
                vision=a.vision,
                actor_segment=a.actor_segment,
            )

    async def create_actor_segment(
        self, data: ActorSegmentSchema
    ) -> ActorSegmentSchema:
        async with IdentityUoW() as uow:
            a: ActorSegment = await self.actor_service.create_actor_segment(
                uow=uow, actor_segment_data=data
            )
            return ActorSegmentSchema(
                id=a.id,
                label=a.label,
                description=a.description,
            )

    async def get_all_actor_segments(self) -> Sequence[ActorSegmentSchema]:
        async with IdentityUoW() as uow:
            actor_segments: Sequence[ActorSegment] = await uow.actor_segments.get_all()

            return [
                ActorSegmentSchema(
                    id=a.id,
                    label=a.label,
                    description=a.description,
                )
                for a in actor_segments
            ]

    async def get_one_actor_segment(self, id: UUID) -> ActorSegmentSchemaRel:
        async with IdentityUoW() as uow:
            a: ActorSegment = await uow.actor_segments.get_by_id(id=id)

            return ActorSegmentSchemaRel(
                id=a.id,
                label=a.label,
                description=a.description,
                actors=[
                    ActorSchema(
                        id=actor.id,
                        label=actor.label,
                        description=actor.description,
                        mission=actor.mission,
                        vision=actor.vision,
                    )
                    for actor in a.actors
                ]
                if a.actors
                else None,
            )
