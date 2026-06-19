from shared.db import UnitOfWork
from ..repositories import (
    ActorRepository,
    ActorSegmentRepository,
    UserActorLinkRepository,
)


class IdentityUoW(UnitOfWork):
    """
    Unit of Work for Identity/Actor Context.
    Handles actor management and segmentation.
    """

    actors: ActorRepository
    user_actor_links: UserActorLinkRepository
    actor_segments: ActorSegmentRepository

    async def __aenter__(self):
        await super().__aenter__()
        assert self.session is not None

        self.actors = ActorRepository(self.session)
        self.user_actor_links = UserActorLinkRepository(self.session)
        self.actor_segments = ActorSegmentRepository(self.session)
        return self

