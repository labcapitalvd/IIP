from pydantic import Field

from shared_schemas import UuidSchema, LabelSchema, DescriptionSchema


###############################################################################
# ActorSegment
###############################################################################
class ActorSegmentSchema(UuidSchema, LabelSchema, DescriptionSchema):
    """Modelo para representar un mensaje de respuesta estandarizado."""

###############################################################################
# Actor
###############################################################################
class ActorSchema(UuidSchema, LabelSchema, DescriptionSchema):
    """Modelo para representar un mensaje de respuesta estandarizado."""

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

