from shared.utils import BaseDomainError


# -----------------------------------------------------------------------------
# Base Auth Error
# -----------------------------------------------------------------------------
class AuthError(BaseDomainError):
    """Base error for authentication/authorization service issues."""

    status_code = 401
    message = "Authentication error."


class UserTierDoesntExist(AuthError):
    """System configuration error - missing default tier in DB."""

    status_code = 500
    message = "Default user tier not found, cannot register user."


class InvalidCredentials(AuthError):
    """Received invalid credentials (username, password, or hash mismatch)."""

    status_code = 401
    message = "Username or password is incorrect."


class UserAlreadyExists(AuthError):
    """Registration collision on existing username or email."""

    status_code = 400
    message = "User already exists."


class UserInactive(AuthError):
    """User account exists but is disabled or inactive."""

    status_code = 403
    message = "User account is disabled or inactive."


# -----------------------------------------------------------------------------
# Token-Specific Domain Errors
# -----------------------------------------------------------------------------
class TokenError(AuthError):
    """Base exception for all token processing issues."""

    status_code = 401
    message = "Authentication token error."


class TokenRevoked(TokenError):
    """Token session is marked inactive or missing from persistence."""

    message = "This token has been revoked and is no longer valid."


class TokenExpired(TokenError):
    """Token or session has passed its expiration time."""

    message = "Your session has expired. Please log in again."


class TokenMalformed(TokenError):
    """Token cannot be parsed, has bad signatures, or lacks required claims."""

    message = "The provided token is malformed or invalid."
