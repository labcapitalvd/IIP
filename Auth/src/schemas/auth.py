from pydantic import EmailStr, Field, SecretStr, field_validator
from shared.schemas import (
    UUID_STR,
    BaseSchema,
    UserEmailSchema,
    UsernameSchema,
    UserPasswordSchema,
    UuidSchema,
)
from shared.utils import sanitize_text, sanitize_email

##############################################################################################
# Requests
##############################################################################################


class RequestRegister(UsernameSchema, UserEmailSchema, UserPasswordSchema):
    """Request body for registering a new user."""

    actor_id: str | None = Field(
        default=None,
        description="UUID of the Actor (distrital entity) this user belongs to, if any.",
    )
    contact_person: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Full name of the contact person for this account.",
    )
    phone: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Contact phone number.",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return sanitize_text(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: EmailStr) -> str:
        return sanitize_email(str(v))

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: SecretStr) -> SecretStr:
        return v


class RequestLogin(UsernameSchema, UserPasswordSchema):
    """Request body for logging in a user."""

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return sanitize_text(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: SecretStr) -> SecretStr:
        return v


class RefreshTokenBody(BaseSchema):
    refresh_token: str


##############################################################################################
# Responses
##############################################################################################


class ResponseMeActorLink(BaseSchema):
    """A single entity membership for the authenticated user (ReBAC)."""

    actor_id: UUID_STR
    actor_label: str
    resource_role: str | None = Field(
        default=None, description="ResourceRole code within this actor, if any."
    )


class ResponseMe(UuidSchema):
    """Authenticated user's profile, resolved fresh from the database."""

    username: str
    email: str
    is_active: bool
    is_verified: bool
    tier: str | None = Field(default=None, description="UserTier code.")
    system_roles: list[str] = Field(
        default_factory=list, description="Global RBAC SystemRole codes."
    )
    actor_links: list[ResponseMeActorLink] = Field(default_factory=list)
    name: str | None = Field(default=None, description="Contact person's full name.")
    phone: str | None = Field(default=None, description="Contact phone number.")
