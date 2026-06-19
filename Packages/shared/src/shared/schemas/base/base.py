from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake
from pydantic import functional_validators, BeforeValidator
from typing import Annotated, Any


def coerce_to_str(v: Any) -> str:
    if isinstance(v, UUID):
        return str(v)
    return v


UUID_STR = Annotated[str, BeforeValidator(coerce_to_str)]


##############################################################################################
# Base
##############################################################################################
class BaseSchema(BaseModel):
    """Modelo base para todas las clases de esquema."""

    model_config = ConfigDict(
        validate_by_name=True,
        alias_generator=to_snake,
    )


##############################################################################################
# Message
##############################################################################################
class ResponseMessageSchema(BaseSchema):
    """Modelo para representar un mensaje de respuesta estandarizado."""

    status: str = Field(
        default="success",
        min_length=1,
        max_length=256,
        title="Status.",
        description="Estado de la respuesta (success/error)",
    )
    code: str = Field(
        default="OK",
        min_length=1,
        max_length=100,
        title="Code.",
        description="Código de negocio (ej: USER_CREATED, LOGOUT_OK)",
    )
    message: str = Field(
        default=...,
        min_length=1,
        max_length=256,
        title="Mensaje.",
        description="Mensaje legible para el usuario",
    )
    detail: str | None = Field(
        default=None,
        min_length=1,
        max_length=4096,
        title="Detalles.",
        description="Detalles de la respuesta",
    )


##############################################################################################
# ID
##############################################################################################
class UuidSchema(BaseSchema):
    """Modelo para representar un UUID."""

    id: UUID_STR | None = Field(
        default=...,
        title="UUID del objeto.",
        description="el UUID en v4 o v7 de un objeto en la db",
    )


##############################################################################################
# Name
##############################################################################################
class LabelSchema(BaseSchema):
    """Modelo para representar un UUID."""

    label: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="Name del objeto.",
        description="el name o label de un objeto en la db",
    )


##############################################################################################
# Description
##############################################################################################
class DescriptionSchema(BaseSchema):
    """Modelo para representar un UUID."""

    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=4096,
        title="Description del objeto.",
        description="el description de un objeto en la db",
    )


##############################################################################################
# Helper
##############################################################################################
class HelperSchema(BaseSchema):
    """Modelo para representar un Helper."""

    helper: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="Helper del objeto.",
        description="el helper de un objeto en la db",
    )


##############################################################################################
# Display Order
##############################################################################################
class DisplayOrderSchema(BaseSchema):
    """Modelo para representar un Display Order."""

    display_order: int | None = Field(
        default=...,
        ge=0,
        le=10000,
        title="Display Order.",
        description="el display_order de un objeto en la db",
    )


##############################################################################################
# Required
##############################################################################################
class RequiredSchema(BaseSchema):
    """Modelo para representar un Required."""

    required: bool | None = Field(
        default=None,
        title="Required.",
        description="el required de un objeto en la db",
    )
