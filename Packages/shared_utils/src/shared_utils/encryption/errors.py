class EncryptionError(Exception):
    """Base error for EncryptionUtils."""


class DecryptionError(Exception):
    """Base error for DecryptionUtils."""


class EmptyEncryptionTarget(EncryptionError):
    """Enrcyption target cannot be empty"""


class EmptyDecryptionTarget(DecryptionError):
    """Decryption target cannot be empty"""
