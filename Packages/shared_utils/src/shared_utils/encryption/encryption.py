from cryptography.fernet import Fernet

from shared_utils.logger import get_logger

from .config import FERNET_PASSWORD
from .errors import (
    EncryptionError,
    DecryptionError,
    EmptyEncryptionTarget,
    EmptyDecryptionTarget,
)


logger = get_logger(__name__)
_cipher = Fernet(FERNET_PASSWORD)


def encrypt(text: str) -> str:
    if not text or not text.strip():
        raise EmptyEncryptionTarget("Cannot encrypt empty string")

    try:
        return _cipher.encrypt(text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise EncryptionError("Encryption failed") from e


def decrypt(token: str) -> str:
    if not token or not token.strip():
        raise EmptyDecryptionTarget("Cannot decrypt empty string")

    try:
        return _cipher.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise DecryptionError("Decryption failed") from e
