from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from typing import Callable

from shared.utils.logger import get_logger
from shared.infrastructure.postgres import sync_engine, async_engine

logger = get_logger(__name__)

SessionSync = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)

SessionAsync = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionAsync() as session:
        yield session


class UnitOfWork:
    """
    Generic async Unit of Work pattern engine.
    Inherited contextually by localized apps to wrap domain repositories.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession] = SessionAsync):
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self):
        self.session = self._session_factory()
        self._init_repositories()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.session:
            return

        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()

    def _init_repositories(self) -> None:
        """Override this in container subclasses to safely bind repositories."""
        pass
