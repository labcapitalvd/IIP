from shared_utils import BaseDomainError


class TokenError(BaseDomainError):
    """Base for all token issues. Default to 401."""

    status_code = 401
    message = "Authentication token error."


class TokenRevoked(TokenError):
    """Token has been revoked."""

    message = "This token has been revoked and is no longer valid."


class TokenExpired(TokenError):
    """Token is no longer valid."""

    message = "Your session has expired. Please log in again."


class TokenMalformed(TokenError):
    """Token does not contain required claims."""

    message = "The provided token is malformed or invalid."
