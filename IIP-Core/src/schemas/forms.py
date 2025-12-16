from typing import Annotated, Optional
from annotated_types import Len
from pydantic import Field

from shared_schemas import BaseSchema, UuidSchema

##############################################################################################
# Requests
##############################################################################################


class RequestForm(UuidSchema):
    """Modelo para representar una solicitud de índice."""
    detailed: bool = Field(
        False, description="Determinar si se desea obtener información detallada o simple."
    )


##############################################################################################
# Responses
##############################################################################################


class ResponseForm(UuidSchema):
    """Modelo para representar una edición de índice de forma resumida."""

    anno: int = Field(..., ge=1900, le=2100, description="Año del índice")
    name: Optional[str] = Field(
        None, min_length=1, max_length=512, description="Nombre del índice"
    )
    description: Optional[str] = Field(
        None, min_length=1, max_length=4096, description="Descripción del índice"
    )
    data: Optional[str] = Field(
        None, min_length=1, max_length=4096, description="Datos del índice"
    )


class ResponseForms(BaseSchema):
    """Modelo para representar una lista de índices de forma resumida."""

    form_editions: Annotated[list[ResponseForm], Len(min_length=1, max_length=512)] = (
        Field(..., description="Lista de índices")
    )
