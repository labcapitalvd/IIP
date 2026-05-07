from uuid import UUID
from typing import Sequence, Annotated
from annotated_types import Len
from pydantic import Field

from shared_schemas import UUID_STR, UuidSchema, LabelSchema, DescriptionSchema


###############################################################################
# Base
###############################################################################
class ActorSchema(UuidSchema, LabelSchema, DescriptionSchema):
    """Modelo para representar un actor."""

    mission: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="Misión.",
        description="Misión del actor.",
    )
    vision: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="Visión",
        description="Visión del actor.",
    )


class ActorSegmentSchema(UuidSchema, LabelSchema, DescriptionSchema):
    """Modelo para representar un actor segment."""


###############################################################################
# Actor
###############################################################################


class ActorSchemaFK(ActorSchema):
    """Modelo para representar un actor."""

    actor_segment_id: UUID_STR | None = Field(
        default=None,
        title="Segmento.",
        description="Segmento al que pertenece el actor.",
    )
    contact_person_id: UUID_STR | None = Field(
        default=None,
        title="Contacto.",
        description="Persona de contacto del actor.",
    )


class ActorSchemaRel(ActorSchema):
    """Modelo para representar un actor."""

    actor_segment: ActorSegmentSchema | None = None
    # user_links: (
    #     Annotated[Sequence[UserActorLinkSchema], Len(min_length=1, max_length=512)] | None
    # ) = Field(None, description="Lista de userlinks")


class ActorSchemaExtended(ActorSchemaFK, ActorSchemaRel):
    """Modelo para representar un actor."""


###############################################################################
# ActorSegment
###############################################################################


class ActorSegmentSchemaFK(ActorSegmentSchema):
    """Modelo para representar un actor segment."""


class ActorSegmentSchemaRel(ActorSegmentSchema):
    """Modelo para representar un actor segment."""

    actors: (
        Annotated[Sequence[ActorSchema], Len(min_length=1, max_length=512)] | None
    ) = Field(None, description="Lista de actores")


class ActorSegmentSchemaExtended(ActorSegmentSchemaFK, ActorSegmentSchemaRel):
    """Modelo para representar un actor segment."""
