from typing import Sequence, Annotated
from annotated_types import Len
from pydantic import Field

from shared_schemas import UuidSchema, LabelSchema, DescriptionSchema


###############################################################################
# Actor
###############################################################################
class ActorSchema(UuidSchema, LabelSchema, DescriptionSchema):
    """Modelo para representar un actor."""

    actor_segment: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="Mensaje desde la API.",
        description="Mensaje legible para el usuario",
    )
    mission: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="Mensaje desde la API.",
        description="Mensaje legible para el usuario",
    )
    vision: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="Mensaje desde la API.",
        description="Mensaje legible para el usuario",
    )


###############################################################################
# ActorSegment
###############################################################################
class ActorSegmentSchema(UuidSchema, LabelSchema, DescriptionSchema):
    """Modelo para representar un actor segment."""

    actors: (
        Annotated[Sequence[ActorSchema], Len(min_length=1, max_length=512)] | None
    ) = Field(None, description="Lista de actores")
