from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from shared.infrastructure.postgres import async_engine, sync_engine
from shared.utils.logger import getLogger

logger = getLogger(__name__)

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

    def __init__(
        self, session_factory: Callable[[], AsyncSession] = SessionAsync
    ) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None
        self._after_commit_hooks: list[Callable[[], Awaitable[Any]]] = []

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()
        self._init_repositories()
        return self

    def add_post_commit_hook(self, hook: Callable[[], Awaitable[Any]]) -> None:
        """Safely queue a background task (e.g., Valkey update) to fire post-commit."""
        self._after_commit_hooks.append(hook)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self.session:
            return

        try:
            if exc_type:
                await self.session.rollback()
                logger.debug("PostgreSQL transaction rolled back due to error.")
            else:
                await self.session.commit()
                logger.debug("PostgreSQL transaction committed successfully.")

                for hook in self._after_commit_hooks:
                    try:
                        await hook()
                    except Exception as hook_exc:
                        logger.error(
                            "Failed to execute post-commit hook: %s",
                            hook_exc,
                            exc_info=True,
                        )
        finally:
            await self.session.close()
            self._after_commit_hooks.clear()

    def _init_repositories(self) -> None:
        """Override this in container subclasses to safely bind repositories."""
        pass
