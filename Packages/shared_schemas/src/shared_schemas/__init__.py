# shared_schemas/__init__.py
# Unified exports for schemas, avoiding circular imports.

from .base.base import (
    BaseSchema,
    UuidSchema,
    ResponseMessage,
)

# auth depends on base, so import it *after* base
from .auth.auth import (
    Username,
    UserEmail,
    UserPassword,
    Platform,
    AccessToken,
    RefreshToken,
    ResponseAuth,
)

__all__ = [
    # base
    "BaseSchema",
    "UuidSchema",
    "ResponseMessage",
    # auth
    "Username",
    "UserEmail",
    "UserPassword",
    "Platform",
    "AccessToken",
    "RefreshToken",
    "ResponseAuth",
    # errors
    "CustomError",
    "ItemError",
    "ResponseError",
    "custom_error_handler",
    "add_custom_error_responses",
    "add_routers_with_custom_errors",
]
