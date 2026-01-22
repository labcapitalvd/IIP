from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.actors import ActorDb

from schemas.actors import (
    ResponseActor,
    ResponseActors,
)

from shared_utils import TextUtils


class ActorHandler:
    def __init__(self, db: AsyncSession, current_user: UUID):
        self.db = db

        self.textutils = TextUtils()
        self.actorondb = ActorDb(self.db)

    async def ActorRead(self, id: UUID, detailed: bool = False) -> ResponseActor:
        actor = await self.actorondb.get_actor_entry(id=id)
        if detailed:
            return ResponseActor(
                id=actor.id,
                name=actor.name,
                description=actor.description,
                actor_segment=actor.actor_segment.name,
                mission=actor.mission,
                vision=actor.vision,
            )
        else:
            return ResponseActor(
                id=actor.id,
                name=actor.name,
            )

    async def ActorReadAll(self, detailed: bool = False) -> ResponseActors:
        actorqueries = await self.actorondb.get_all_actor_entries()
        if detailed:
            return ResponseActors(
                actors=[
                    ResponseActor(
                        id=i.id,
                        name=i.name,
                        description=i.description,
                        actor_segment=i.actor_segment.name,
                        mission=i.mission,
                        vision=i.vision,
                    )
                    for i in actorqueries
                ]
            )
        else:
            return ResponseActors(
                actors=[ResponseActor(id=i.id, name=i.name) for i in actorqueries]
            )
