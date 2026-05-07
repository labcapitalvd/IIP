from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake


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
# ID
##############################################################################################
class UuidSchema(BaseSchema):
    """Modelo para representar un UUID."""

    id: UUID | None = Field(
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
        max_length=256,
        title="Description del objeto.",
        description="el description de un objeto en la db",
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
        title="Status desde la API.",
        description="Estado de la respuesta (success/error)",
    )
    code: str = Field(
        default="OK",
        min_length=1,
        max_length=100,
        title="Código desde la API.",
        description="Código de negocio (ej: USER_CREATED, LOGOUT_OK)",
    )
    message: str = Field(
        default=...,
        min_length=1,
        max_length=256,
        title="Mensaje desde la API.",
        description="Mensaje legible para el usuario",
    )
