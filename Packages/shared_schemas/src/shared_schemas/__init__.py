# shared_schemas/__init__.py
# Unified exports for schemas, avoiding circular imports.

from .base.base import (
    BaseSchema,
    UuidSchema,
    LabelSchema,
    DescriptionSchema,
    ResponseMessageSchema,
)

# auth depends on base, so import it *after* base
from .auth.auth import (
    UsernameSchema,
    UserEmailSchema,
    UserPasswordSchema,
    PlatformSchema,
    AccessTokenSchema,
    RefreshTokenSchema,
    ResponseAuthSchema,
)

from .core.actors import (
    ActorSchema,
    ActorSegmentSchema,
)

__all__ = [
    # errors
    "CustomError",
    "ItemError",
    "ResponseError",
    "custom_error_handler",
    "add_custom_error_responses",
    "add_routers_with_custom_errors",
    # base
    "BaseSchema",
    "UuidSchema",
    "LabelSchema",
    "DescriptionSchema",
    "ResponseMessageSchema",
    # auth
    "UsernameSchema",
    "UserEmailSchema",
    "UserPasswordSchema",
    "PlatformSchema",
    "AccessTokenSchema",
    "RefreshTokenSchema",
    "ResponseAuthSchema",
    # core
    "ActorSchema",
    "ActorSegmentSchema",
]
