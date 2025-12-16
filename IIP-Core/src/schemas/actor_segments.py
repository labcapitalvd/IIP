from typing import Annotated, Optional
from annotated_types import Len
from pydantic import Field

from schemas.actors import ResponseActor

from shared_schemas import BaseSchema, UuidSchema

##############################################################################################
# Requests
##############################################################################################


class RequestActorSegment(UuidSchema):
    """Modelo para representar una solicitud de actor_segment."""
    detailed: bool = Field(
        False, description="Determinar si se desea obtener información detallada o simple."
    )


##############################################################################################
# Responses
##############################################################################################


class ResponseActorSegment(UuidSchema):
    """Modelo para representar una solicitud de actor_segment."""

    name: str = Field(
        ..., min_length=1, max_length=512, description="Nombre del actor_segment"
    )
    description: Optional[str] = Field(
        None, min_length=1, max_length=4096, description="Descripción del actor_segment"
    )
    actors: Optional[Annotated[list[ResponseActor], Len(min_length=1, max_length=512)]] = Field(
        None, description="Lista de actores"
    )


class ResponseActorSegments(BaseSchema):
    """Modelo para representar una lista de actor_segmentes de forma resumida."""

    actor_segments: Annotated[
        list[ResponseActorSegment], Len(min_length=1, max_length=512)
    ] = Field(..., description="Lista de actor_segmentes")
