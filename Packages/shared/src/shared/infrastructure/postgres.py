import os

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from shared.utils.logger import get_logger

logger = get_logger(__name__)

POSTGRES_USER = os.getenv("POSTGRES_USER", "app_user")
POSTGRES_DB = os.getenv("POSTGRES_DB", "app")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_PASSWORD_FILE = "/run/secrets/postgres_password"


def load_postgres_key() -> str:
    if not os.path.exists(POSTGRES_PASSWORD_FILE):
        logger.critical("Postgress pass missing at %s", POSTGRES_PASSWORD_FILE)
        raise RuntimeError(
            "Postgress pass not configured. Mount /run/secrets/postgres_password"
        )

    with open(POSTGRES_PASSWORD_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
        if len(key) <= 0:
            logger.critical("Invalid Postgress pass length (%d)", len(key))
            raise RuntimeError("Invalid Postgress pass")
        return key


POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD") or load_postgres_key()

logger.debug(f"""
user:{POSTGRES_USER}
pass:{"*" * len(str(POSTGRES_PASSWORD))}
host:{POSTGRES_HOST}
port:{POSTGRES_PORT}
db:  {POSTGRES_DB}""")

SYNC_DB = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
ASYNC_DB = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

sync_engine = create_engine(SYNC_DB)
async_engine = create_async_engine(ASYNC_DB)
