from uuid import UUID

from typing import Sequence, Annotated
from annotated_types import Len
from pydantic import Field

from shared_schemas import (
    UuidSchema,
    LabelSchema,
    DescriptionSchema,
    HelperSchema,
    DisplayOrderSchema,
    RequiredSchema,
)


###############################################################################
# Base
###############################################################################


class CardTemplateSchema(UuidSchema, LabelSchema, DescriptionSchema, HelperSchema):
    """Modelo para representar un CardTemplate."""


class FieldSchema(
    UuidSchema, LabelSchema, DescriptionSchema, RequiredSchema, DisplayOrderSchema
):
    """Modelo para representar un Field."""


class FieldChoiceSchema(UuidSchema, LabelSchema, DescriptionSchema, DisplayOrderSchema):
    """Modelo para representar un FieldChoice."""


class FieldGroupSchema(UuidSchema, LabelSchema, DescriptionSchema, DisplayOrderSchema):
    """Modelo para representar un FieldGroup."""


class FormSchema(UuidSchema, LabelSchema, DescriptionSchema):
    """Modelo para representar un Form."""

    anno: int = Field(
        default=...,
        min_length=1,
        max_length=4,
        title="Año del formulario.",
        description="Mensaje legible para el usuario",
    )


class InfoSchema(UuidSchema, LabelSchema, DescriptionSchema, DisplayOrderSchema):
    """Modelo para representar un Info."""


class QuestionSchema(
    UuidSchema,
    LabelSchema,
    DescriptionSchema,
    HelperSchema,
    DisplayOrderSchema,
    RequiredSchema,
):
    """Modelo para representar un Question."""

    is_loop: bool | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="Is Loop.",
        description="Booleana de si pregunta es un bucle.",
    )


class SectionSchema(
    UuidSchema, LabelSchema, DescriptionSchema, HelperSchema, DisplayOrderSchema
):
    """Modelo para representar un Section."""


class SectionTypeSchema(UuidSchema, LabelSchema, DescriptionSchema):
    """Modelo para representar un Section."""


###############################################################################
# CardTemplate
###############################################################################


class CardTemplateSchemaFK:
    """Modelo para representar un CardTemplate."""

    question_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de question.",
    )


class CardTemplateSchemaRel:
    """Modelo para representar un CardTemplate."""


class CardTemplateSchemaExtended:
    """Modelo para representar un CardTemplate."""


###############################################################################
# Field
###############################################################################


class FieldSchemaFK:
    """Modelo para representar un Field."""

    form_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de question.",
    )
    field_group_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de question.",
    )
    field_type_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de question.",
    )


class FieldSchemaRel:
    """Modelo para representar un Field."""


class FieldSchemaExtended:
    """Modelo para representar un Field."""


###############################################################################
# FieldChoice
###############################################################################


class FieldChoiceSchemaFK:
    """Modelo para representar un FieldChoice."""


class FieldChoiceSchemaRel:
    """Modelo para representar un FieldChoice."""


class FieldChoiceSchemaExtended:
    """Modelo para representar un FieldChoice."""


###############################################################################
# FieldGroup
###############################################################################


class FieldGroupSchemaFK:
    """Modelo para representar un FieldGroup."""


class FieldGroupSchemaRel:
    """Modelo para representar un FieldGroup."""


class FieldGroupSchemaExtended:
    """Modelo para representar un FieldGroup."""


###############################################################################
# Form
###############################################################################


class FormSchemaFK:
    """Modelo para representar un Form."""


class FormSchemaRel:
    """Modelo para representar un Form."""


class FormSchemaExtended:
    """Modelo para representar un Form."""


###############################################################################
# Info
###############################################################################


class InfoSchemaFK:
    """Modelo para representar un Info."""


class InfoSchemaRel:
    """Modelo para representar un Info."""


class InfoSchemaExtended:
    """Modelo para representar un Info."""


###############################################################################
# Question
###############################################################################


class QuestionSchemaFK:
    """Modelo para representar un Question."""


class QuestionSchemaRel:
    """Modelo para representar un Question."""


class QuestionSchemaExtended:
    """Modelo para representar un Question."""


###############################################################################
# Section
###############################################################################


class SectionSchemaFK:
    """Modelo para representar un Section."""


class SectionSchemaRel:
    """Modelo para representar un Section."""


class SectionSchemaExtended:
    """Modelo para representar un Section."""


###############################################################################
# Section Type
###############################################################################


class SectionTypeSchemaFK:
    """Modelo para representar un Section."""


class SectionTypeSchemaRel:
    """Modelo para representar un Section."""


class SectionTypeSchemaExtended:
    """Modelo para representar un Section."""
