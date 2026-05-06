from shared_schemas import ActorSchema, ActorSegmentSchema, ResponseActorSchema
from sqlalchemy import label, select
from sqlalchemy.orm import selectinload
from typing import List, Any
from uuid import UUID

from shared_models import Submission, Answer, AnswerCardEntry, Actor
from domain.factories.answer_factory import AnswerFactory
from infrastructure.uow import IdentityUoW

from shared_models.enums import SubmissionStatusesEnum

from .errors import ActorError, ActorAlreadyExistsError, SegmentNotFoundError


class ActorService:
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

        segment = await uow.segments.get_by_label(label=actor_data.actor_segment)

        if not segment:
            raise SegmentNotFoundError(actor_data.actor_segment)

        data_for_db = actor_data.model_dump(exclude={"id", "actor_segment"})

        actor = Actor(actor_segment_id=segment.id, **data_for_db)

        uow.actors.add(actor)
        return actor 

