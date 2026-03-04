class TextError(Exception):
    """Base error for TextUtils."""


class TextEmpty(TextError):
    """Text target is empty"""


class TextMalformed(TextError):
    """Text flagged as malformed"""
