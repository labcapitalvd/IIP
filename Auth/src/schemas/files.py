from typing import Annotated

from annotated_types import Len
from pydantic import Field
from shared_schemas import UuidSchema

##############################################################################################
# Requests
##############################################################################################


class RequestEditFile(UuidSchema):
    """Schema para editar archivo basado en UUID."""

    filename: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Recibe el nuevo nombre del archivo",
    )


##############################################################################################
# Responses
##############################################################################################


class ResponseFiles(UuidSchema):
    """Modelo para representar un listado de archivos de respuesta."""

    files: Annotated[list[str], Len(min_length=1, max_length=512)] = Field(
        ..., description="Lista de archivos"
    )
