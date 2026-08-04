# Packages/shared/src/shared/infra/valkey.py
import os
import valkey.asyncio as aiovalkey
from shared.utils.logger import get_logger

logger = get_logger(__name__)

VALKEY_USER = os.getenv("VALKEY_USER", "valkey_user")
VALKEY_DB = os.getenv("VALKEY_DB", "app_cache")
VALKEY_HOST = os.getenv(
    "VALKEY_HOST", "cache"
)  # Defaulting to a valkey container service name
VALKEY_PORT = os.getenv("VALKEY_PORT", "6379")
VALKEY_PASSWORD_FILE = "/run/secrets/valkey_password"


def load_valkey_key() -> str:
    if not os.path.exists(VALKEY_PASSWORD_FILE):
        logger.critical("Valkey pass missing at %s", VALKEY_PASSWORD_FILE)
        raise RuntimeError(
            "Valkey pass not configured. Mount /run/secrets/valkey_password"
        )

    with open(VALKEY_PASSWORD_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
        if len(key) <= 0:
            logger.critical("Invalid Valkey pass length (%d)", len(key))
            raise RuntimeError("Invalid Valkey pass")
        return key


env_key = os.getenv("VALKEY_PASSWORD")

# Ensure FERNET_PASSWORD is always bytes
if env_key:
    vk_pass = env_key.encode()
else:
    vk_pass = load_valkey_key()

VALKEY_PASSWORD = vk_pass


logger.debug(f"""
user:{VALKEY_USER}
pass:{"*" * len(str(VALKEY_PASSWORD))}
host:{VALKEY_HOST}
port:{VALKEY_PORT}
db:  {VALKEY_DB}""")

# Build the connection string URL using standard wire protocol compatible with Valkey
if VALKEY_PASSWORD:
    VALKEY_URL = f"redis://{VALKEY_USER}:{VALKEY_PASSWORD}@{VALKEY_HOST}:{VALKEY_PORT}/{VALKEY_DB}"
else:
    VALKEY_URL = f"redis://{VALKEY_HOST}:{VALKEY_PORT}/{VALKEY_DB}"

# Initialize the persistent client pool instance targeting Valkey
valkey_client = aiovalkey.from_url(VALKEY_URL, decode_responses=True)
