from pydantic import EmailStr, SecretStr, field_validator
from shared_schemas import (
    BaseSchema,
    UserEmail,
    Username,
    UserPassword,
)
from shared_utils import sanitize_text, sanitize_email

##############################################################################################
# Requests
##############################################################################################


class RequestRegister(Username, UserEmail, UserPassword):
    """Request body for registering a new user."""

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


class RequestLogin(Username, UserPassword):
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
