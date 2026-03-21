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

    id: UUID = Field(
        ...,
        title="UUID del objeto.",
        description="el UUID en v4 o v7 de un objeto en la db",
    )


##############################################################################################
# Message
##############################################################################################
class ResponseMessage(BaseSchema):
    """Modelo para representar un mensaje de respuesta estandarizado."""

    status: str = Field(
        "success",
        min_length=1,
        max_length=256,
        title="Status desde la API.",
        description="Estado de la respuesta (success/error)",
    )
    code: str = Field(
        "OK",
        min_length=1,
        max_length=100,
        title="Código desde la API.",
        description="Código de negocio (ej: USER_CREATED, LOGOUT_OK)",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=256,
        title="Mensaje desde la API.",
        description="Mensaje legible para el usuario",
    )
