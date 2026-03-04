from shared_utils import BaseDomainError


class AuthError(BaseDomainError):
    """Base error for auth service errors."""

    status_code = 401
    message = "Authentication error."


class TierDoesntExist(AuthError):
    """System configuration error."""

    status_code = 500
    message = "Default user tier not found, cannot register user."


class InvalidCredentials(AuthError):
    """Received invalid credentials."""

    message = "Username or password is incorrect."


class UserAlreadyExists(AuthError):
    """User already exists."""

    status_code = 400
    message = "User already exists."
