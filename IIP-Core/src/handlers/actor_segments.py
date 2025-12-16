from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.actor_segments import ActorSegmentDb

from schemas.actor_segments import ResponseActorSegment, ResponseActorSegments
from schemas.actors import ResponseActor

from shared_utils import TextUtils


class ActorSegmentHandler:
    def __init__(self, db: AsyncSession, current_user: UUID):
        self.db = db

        self.textutils = TextUtils()
        self.actor_segmentondb = ActorSegmentDb(self.db)

    async def ActorSegmentRead(self, id: UUID, detailed: bool = False) -> ResponseActorSegment:
        actor_segment = await self.actor_segmentondb.get_actor_segment_entry(id=id)
        if detailed:
            return ResponseActorSegment(
                id=actor_segment.id,
                name=actor_segment.name,
                description=actor_segment.description,
                actors=[ResponseActor(
                    id=i.id,
                    name=i.name,
                    description=i.description,
                    actor_segment=i.actor_segment.name,
                    mission=i.mission,
                    vision=i.vision,
                ) for i in actor_segment.actors],
            )
        else:
            return ResponseActorSegment(
                id=actor_segment.id,
                name=actor_segment.name,
            )

    async def ActorSegmentReadAll(self, detailed: bool = False) -> ResponseActorSegments:
        actor_segmentqueries = await self.actor_segmentondb.get_all_actor_segment_entries()
        if detailed:
            return ResponseActorSegments(
                actor_segments=[
                    ResponseActorSegment(
                        id=i.id,
                        name=i.name,
                        description=i.description,
                        actors=[ResponseActor(
                            id=j.id,
                            name=j.name,
                            description=j.description,
                            actor_segment=j.actor_segment.name,
                            mission=j.mission,
                            vision=j.vision,
                        ) for j in i.actors],
                    )
                    for i in actor_segmentqueries
                ]
            )
        else:
            return ResponseActorSegments(
                actor_segments=[
                    ResponseActorSegment(
                        id=i.id,
                        name=i.name,
                    )
                    for i in actor_segmentqueries
                ]
            )
