from shared_db import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

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

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.actors = ActorRepository(session)
        self.user_actor_links = UserActorLinkRepository(session)
        self.segments = ActorSegmentRepository(session)
