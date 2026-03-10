class TokenError(Exception):
    """Base error for TokenUtils."""


class TokenEncodeError(TokenError):
    """Token encode error."""


class TokenDecodeError(TokenError):
    """Token decode error."""


class TokenExpiredError(TokenError):
    """Expired token error."""


class TokenSignatureError(TokenError):
    """Wrong token signature error."""


class TokenEmptyError(TokenError):
    """Empty token error."""


class TokenTypeError(TokenError):
    """Wrong token type error."""


class InvalidPlatformError(TokenError):
    """Unsupported platform error."""
