from shared_schemas import (
    ActorSchema,
    ActorSegmentSchema,
    ActorSchemaRel,
    ActorSchemaFK,
    UuidSchema,
)
from sqlalchemy import label, select
from sqlalchemy.orm import selectinload
from typing import List, Any
from uuid import UUID

from shared_models import Submission, Answer, AnswerCardEntry, Actor, ActorSegment
from domain.factories.answer_factory import AnswerFactory
from infrastructure.uow import IdentityUoW

from .errors import (
    ActorError,
    ActorSegmentError,
    ActorAlreadyExistsError,
    ActorNotFoundError,
    ActorSegmentNotFoundError,
    ActorSegmentAlreadyExistsError,
)


class ActorService:
    async def create_actor(
        self,
        uow: IdentityUoW,
        actor_data: ActorSchemaFK,
    ) -> Actor:
        if not actor_data.label or not actor_data.actor_segment_id:
            raise ValueError("Actor label is required for creation.")

        if await uow.actors.get_by_label(label=actor_data.label):
            raise ActorAlreadyExistsError(actor_data.label)

        seg_id = actor_data.actor_segment_id

        if not seg_id:
            raise ValueError("Actor segment id is required.")

        segment = await uow.actor_segments.get_by_id(id=UUID(seg_id))

        if not segment:
            raise ActorSegmentNotFoundError(seg_id)

        data_for_db = actor_data.model_dump(exclude={"id", "actor_segment_id"})

        actor = Actor(actor_segment=segment, **data_for_db)

        uow.actors.add(actor)
        return actor

    async def delete_actor(
        self,
        uow: IdentityUoW,
        actor_id: UUID,
    ) -> Actor:
        if not actor_id:
            raise ValueError("Actor label is required for creation.")

        existing = await uow.actors.get_by_id(id=actor_id)

        if not existing:
            raise ActorNotFoundError()

        uow.actors.delete(existing)
        return existing

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

        data_for_db = actor_segment_data.model_dump(exclude={"id"})

        actor_segment = ActorSegment(**data_for_db)

        uow.actor_segments.add(actor_segment)
        return actor_segment

    async def delete_actor_segment(
        self,
        uow: IdentityUoW,
        actor_segment_id: UUID,
    ) -> ActorSegment:
        if not actor_segment_id:
            raise ValueError("Actor label is required for creation.")

        existing = await uow.actor_segments.get_by_id(id=actor_segment_id)

        if not existing:
            raise ActorSegmentNotFoundError()

        uow.actor_segments.delete(existing)
        return existing
