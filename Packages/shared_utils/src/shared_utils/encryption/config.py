import webencodings
import os

from shared_utils.logger import get_logger

logger = get_logger(__name__)

FERNET_KEY_FILE = "/run/secrets/fernet_password"


def load_fernet_key() -> bytes:
    if not os.path.exists(FERNET_KEY_FILE):
        logger.critical("Fernet key missing at %s", FERNET_KEY_FILE)
        raise RuntimeError(
            "Fernet key not configured. Mount /run/secrets/fernet_password"
        )

    with open(FERNET_KEY_FILE, "rb") as f:
        key = f.read().strip()
        if len(key) != 44:
            logger.critical("Invalid Fernet pass length (%d)", len(key))
            raise RuntimeError("Invalid Fernet pass")
        return key

env_key = os.environ.get("FERNET_PASSWORD")

# Ensure FERNET_PASSWORD is always bytes
if env_key:
    ft_pass = env_key.encode()
else:
    ft_pass = load_fernet_key()

FERNET_PASSWORD = ft_pass

