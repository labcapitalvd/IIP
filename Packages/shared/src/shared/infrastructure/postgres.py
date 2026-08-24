import os

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from shared.utils.logger import getLogger
from shared.utils import format_banner, format_list

logger = getLogger(__name__)

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres_user")
POSTGRES_DB = os.getenv("POSTGRES_DB", "app_db")
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

env_key = os.getenv("POSTGRES_PASSWORD")

# Ensure FERNET_PASSWORD is always bytes
if env_key:
    pg_pass = env_key.encode()
else:
    pg_pass = load_postgres_key()

POSTGRES_PASSWORD = pg_pass

postgres_info = f"""
user:{POSTGRES_USER}
pass:{"*" * len(str(POSTGRES_PASSWORD))}
host:{POSTGRES_HOST}
port:{POSTGRES_PORT}
db:  {POSTGRES_DB}
"""


logger.debug("\n" + format_banner(postgres_info, align="left"))

SYNC_URL = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
ASYNC_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

sync_engine = create_engine(SYNC_URL)
async_engine = create_async_engine(ASYNC_URL)
