from typing import Annotated, Optional
from annotated_types import Len
from pydantic import Field

from shared_schemas import BaseSchema, UuidSchema

##############################################################################################
# Requests
##############################################################################################


class RequestActor(UuidSchema):
    """Modelo para representar una solicitud de entidad."""
    detailed: bool = Field(
        False, description="Determinar si se desea obtener información detallada o simple."
    )


##############################################################################################
# Responses
##############################################################################################


class ResponseActor(UuidSchema):
    """Modelo para representar una solicitud de entidad."""

    name: str = Field(
        ..., min_length=1, max_length=512, description="Nombre de la entidad"
    )
    description: Optional[str] = Field(
        None, min_length=1, max_length=4096, description="Descripción de la entidad"
    )
    actor_segment: Optional[str] = Field(
        None, min_length=1, max_length=512, description="ActorSegment de la entidad"
    )
    mission: Optional[str] = Field(
        None, min_length=1, max_length=4096, description="Misión de la entidad"
    )
    vision: Optional[str] = Field(
        None, min_length=1, max_length=4096, description="Visión de la entidad"
    )


class ResponseActors(BaseSchema):
    """Modelo para representar una lista de entidades de forma resumida."""

    actors: Annotated[list[ResponseActor], Len(min_length=1, max_length=512)] = Field(
        ..., description="Lista de entidades"
    )
