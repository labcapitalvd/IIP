from shared_schemas import (
    ActorSchema,
    ActorSegmentSchema,
    ActorSchemaRel,
    ActorSchemaFK,
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
    ActorAlreadyExistsError,
    SegmentNotFoundError,
    ActorSegmentAlreadyExistsError,
)


class ActorService:
    async def create_actor(
        self,
        uow: IdentityUoW,
        actor_data: ActorSchemaRel,
    ) -> Actor:
        if not actor_data.label:
            raise ValueError("Actor label is required for creation.")

        existing = await uow.actors.get_by_label(label=actor_data.label)

        if existing:
            raise ActorAlreadyExistsError(actor_data.label)

        seg_label = actor_data.actor_segment.label if actor_data.actor_segment else None

        if not seg_label:
            raise ValueError("Actor segment label is required.")

        segment = await uow.actor_segments.get_by_label(
            label=seg_label
        )

        if not segment:
            raise SegmentNotFoundError(seg_label)

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

        data_for_db = actor_segment_data.model_dump(exclude={"id"})

        actor_segment = ActorSegment(**data_for_db)

        uow.actor_segments.add(actor_segment)
        return actor_segment
