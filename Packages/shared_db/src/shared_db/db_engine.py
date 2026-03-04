from shared_utils import encrypt
import os
from typing import AsyncGenerator, Dict, Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from shared_utils.logger import get_logger

logger = get_logger(__name__)

POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_HOST = os.getenv("POSTGRES_HOST","db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT","5432")
POSTGRES_PASSWORD_FILE = "/run/secrets/postgres_password"

def load_postgres_key() -> str:
    if not os.path.exists(POSTGRES_PASSWORD_FILE):
        logger.critical("Postgress pass missing at %s", POSTGRES_PASSWORD_FILE)
        raise RuntimeError("Postgress pass not configured. Mount /run/secrets/postgres_password")

    with open(POSTGRES_PASSWORD_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
        if len(key) <= 0:
            logger.critical("Invalid Postgress pass length (%d)", len(key))
            raise RuntimeError("Invalid Postgress pass")
        return key

POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD") or load_postgres_key()

logger.debug(f"""
user:{POSTGRES_USER}
pass:{'*' * len(str(POSTGRES_PASSWORD))}
host:{POSTGRES_HOST}
port:{POSTGRES_PORT}
db:  {POSTGRES_DB}""")

SYNC_DB = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
ASYNC_DB = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

sync_engine = create_engine(SYNC_DB)
async_engine = create_async_engine(ASYNC_DB)

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
    Generic async Unit of Work.
    Can attach any repositories dynamically.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession] = SessionAsync,):
        self._session_factory = session_factory
        self.session: AsyncSession | None = None
        self.repos: Dict[str, object] = {}

    async def __aenter__(self):
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        assert self.session is not None

        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()

        await self.session.close()
