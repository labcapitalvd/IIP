class HashError(Exception):
    """Base error for HashUtils."""


class EmptyHashTarget(HashError):
    """Empty input provided."""


class HashMismatch(HashError):
    """Value does not match hash."""


class InvalidHashFormat(HashError):
    """Stored hash is invalid or corrupted."""
