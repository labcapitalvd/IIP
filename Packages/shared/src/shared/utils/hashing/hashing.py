from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from .errors import HashError, EmptyHashTarget, HashMismatch, InvalidHashFormat


password_hasher = PasswordHasher(memory_cost=131072, time_cost=3, parallelism=2)
token_hasher = PasswordHasher(memory_cost=65536, time_cost=1, parallelism=1)
fast_hasher = PasswordHasher(memory_cost=16384, time_cost=1, parallelism=1)


def hash_value(hasher: PasswordHasher, value: str) -> str:
    if not value or not value.strip():
        raise EmptyHashTarget("Cannot hash empty string")

    try:
        return hasher.hash(value)
    except Exception as e:
        raise HashError("Hash operation failed") from e


def verify_value(hasher: PasswordHasher, value: str, hashed_value: str) -> None:
    if not value or not value.strip():
        raise EmptyHashTarget("Cannot verify empty string")
    if not hashed_value or not hashed_value.strip():
        raise EmptyHashTarget("Cannot verify empty string")

    try:
        hasher.verify(hashed_value, value)
    except VerifyMismatchError:
        raise HashMismatch("Hash verification failed")
    except VerificationError:
        raise InvalidHashFormat("Unknown or invalid hash format")
    except Exception as e:
        raise HashError("Hash operation failed") from e


def hash_password(password: str) -> str:
    """Hashes a password using the password context."""
    return hash_value(password_hasher, password)


def hash_token(token: str) -> str:
    """Hashes a token using the token context."""
    return hash_value(token_hasher, token)


def hash_string(secret: str) -> str:
    """Hashes a string using the fast context."""
    return hash_value(fast_hasher, secret)


def verify_password(password: str, hashed_password: str) -> None:
    """Verifies a password using the password context."""
    verify_value(password_hasher, password, hashed_password)
    if password_hasher.check_needs_rehash(hashed_password):
        raise HashError("Rehash of password needed.")


def verify_token(token: str, hashed_token: str) -> None:
    """Verifies a token using the token context."""
    verify_value(token_hasher, token, hashed_token)


def verify_string(secret: str, hashed_secret: str) -> None:
    """Verifies a string using the fast context."""
    verify_value(fast_hasher, secret, hashed_secret)
