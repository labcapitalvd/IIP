from typing import Annotated
from annotated_types import Len
from pydantic import Field
from fastapi import UploadFile

from shared_schemas import UuidSchema

##############################################################################################
# Requests
##############################################################################################


class RequestFile(UuidSchema):
    """Request body for getting a file."""


class RequestCreateFile:
    """Request body for creating a file."""

    file: UploadFile = Field(..., description="Archivo a subir")


class RequestEditFile(UuidSchema):
    """Request body for editing a file."""

    filename: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Recibe el nuevo nombre del archivo",
    )


class RequestDeleteFile(UuidSchema):
    """Request body for deleting a file."""


##############################################################################################
# Responses
##############################################################################################


class ResponseFile(UuidSchema):
    """Modelo para representar un archivo de respuesta."""


class ResponseFiles(ResponseFile):
    """Modelo para representar un listado de archivos de respuesta."""

    files: Annotated[list[str], Len(min_length=1, max_length=512)] = Field(
        ..., description="Lista de archivos"
    )
