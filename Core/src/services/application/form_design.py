from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from domain import FormService
from infrastructure.uow import FormDesignUoW

from shared.models import Actor, ActorSegment
from shared.schemas import ActorSchema, ActorSegmentSchema


class FormDesignAppService:
    def __init__(
        self,
        form_service: FormService | None = None,
    ):
        self.form_service = form_service or FormService()

    async def create_form(self, data: ActorSchema) -> ActorSchema:
        async with FormDesignUoW() as uow:
            a: Actor = await self.form_service.create_form(uow=uow, actor_data=data)
            return ActorSchema(
                id=a.id,
                label=a.label,
                description=a.description,
                actor_segment=a.actor_segment.label,
                mission=a.mission,
                vision=a.vision,
            )

    async def get_all_forms(self) -> Sequence[ActorSchema]:
        async with FormDesignUoW() as uow:
            actors: Sequence[Actor] = await uow.actors.get_all()

            return [
                ActorSchema(
                    id=a.id,
                    label=a.label,
                    description=a.description,
                    actor_segment=a.actor_segment.label,
                    mission=a.mission,
                    vision=a.vision,
                )
                for a in actors
            ]

    async def get_one_form(self, id: UUID) -> ActorSchema:
        async with FormDesignUoW() as uow:
            a: ActorSegment = await uow.actors.get_by_id(id=id)

            return ActorSchema(
                id=a.id,
                label=a.label,
                description=a.description,
                actor_segment=a.actor_segment.label,
                mission=a.mission,
                vision=a.vision,
            )

