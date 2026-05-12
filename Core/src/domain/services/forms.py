from shared_schemas import ActorSchema, ActorSegmentSchema
from sqlalchemy import label, select
from sqlalchemy.orm import selectinload
from typing import List, Any
from uuid import UUID

from shared_models import Submission, Answer, AnswerCardEntry, Actor, ActorSegment
from domain.factories.answer_factory import AnswerFactory
from infrastructure.uow import IdentityUoW

from .errors import ActorError, ActorAlreadyExistsError, ActorSegmentNotFoundError, ActorSegmentAlreadyExistsError


class FormService:
    async def create_actor(
        self,
        uow: IdentityUoW,
        actor_data: ActorSchema,
    ) -> Actor:
        if not actor_data.label or not actor_data.actor_segment:
            raise ValueError("Actor label is required for creation.")

        existing = await uow.actors.get_by_label(label=actor_data.label)

        if existing:
            raise ActorAlreadyExistsError(actor_data.label)

        segment = await uow.actor_segments.get_by_label(label=actor_data.actor_segment)

        if not segment:
            raise ActorSegmentNotFoundError(actor_data.actor_segment)

        data_for_db = actor_data.model_dump(exclude={"id", "actor_segment"})

        actor = Actor(actor_segment=segment, **data_for_db)

        uow.actors.add(actor)
        return actor 

    async def create_actor_segment(
        self,
        uow: IdentityUoW,
        actor_segment_data: ActorSegmentSchema,
    ) -> ActorSegment:
        if not actor_segment_data.label:
            raise ValueError("Actor label is required for creation.")

        existing = await uow.actor_segments.get_by_label(label=actor_segment_data.label)

        if existing:
            raise ActorSegmentAlreadyExistsError(actor_segment_data.label)


        data_for_db = actor_segment_data.model_dump(exclude={"id", "actors"})

        actor_segment = ActorSegment(**data_for_db)

        uow.actor_segments.add(actor_segment)
        return actor_segment

