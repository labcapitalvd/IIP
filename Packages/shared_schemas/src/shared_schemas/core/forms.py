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


class CardTemplateSchemaExtended(
    CardTemplateSchema, CardTemplateSchemaFK, CardTemplateSchemaRel
):
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
        description="Id de formulario.",
    )
    field_group_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de field group.",
    )
    field_type_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de field type.",
    )


class FieldSchemaRel:
    """Modelo para representar un Field."""


class FieldSchemaExtended(FieldSchema, FieldSchemaFK, FieldSchemaRel):
    """Modelo para representar un Field."""


###############################################################################
# FieldChoice
###############################################################################


class FieldChoiceSchemaFK:
    """Modelo para representar un FieldChoice."""

    field_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de field.",
    )


class FieldChoiceSchemaRel:
    """Modelo para representar un FieldChoice."""


class FieldChoiceSchemaExtended(
    FieldChoiceSchema, FieldChoiceSchemaFK, FieldChoiceSchemaRel
):
    """Modelo para representar un FieldChoice."""


###############################################################################
# FieldGroup
###############################################################################


class FieldGroupSchemaFK:
    """Modelo para representar un FieldGroup."""

    form_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de form.",
    )
    question_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de question.",
    )
    card_template_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de card_template.",
    )


class FieldGroupSchemaRel:
    """Modelo para representar un FieldGroup."""


class FieldGroupSchemaExtended(
    FieldGroupSchema, FieldGroupSchemaFK, FieldGroupSchemaRel
):
    """Modelo para representar un FieldGroup."""


###############################################################################
# Form
###############################################################################


class FormSchemaFK:
    """Modelo para representar un Form."""


class FormSchemaRel:
    """Modelo para representar un Form."""


class FormSchemaExtended(FormSchema, FormSchemaFK, FormSchemaRel):
    """Modelo para representar un Form."""


###############################################################################
# Info
###############################################################################


class InfoSchemaFK:
    """Modelo para representar un Info."""

    section_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de section.",
    )
    file_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de file.",
    )


class InfoSchemaRel:
    """Modelo para representar un Info."""


class InfoSchemaExtended(InfoSchema, InfoSchemaFK, InfoSchemaRel):
    """Modelo para representar un Info."""


###############################################################################
# Question
###############################################################################


class QuestionSchemaFK:
    """Modelo para representar un Question."""

    form_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de form.",
    )
    section_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de section.",
    )
    file_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de file.",
    )


class QuestionSchemaRel:
    """Modelo para representar un Question."""


class QuestionSchemaExtended(QuestionSchema, QuestionSchemaFK, QuestionSchemaRel):
    """Modelo para representar un Question."""


###############################################################################
# Section
###############################################################################


class SectionSchemaFK:
    """Modelo para representar un Section."""

    form_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de form.",
    )
    file_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de file.",
    )
    parent_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de parent.",
    )
    section_type_id: UUID | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        title="ID.",
        description="Id de section type.",
    )


class SectionSchemaRel:
    """Modelo para representar un Section."""


class SectionSchemaExtended(SectionSchema, SectionSchemaFK, SectionSchemaRel):
    """Modelo para representar un Section."""


###############################################################################
# Section Type
###############################################################################


class SectionTypeSchemaFK:
    """Modelo para representar un Section."""


class SectionTypeSchemaRel:
    """Modelo para representar un Section."""


class SectionTypeSchemaExtended(
    SectionTypeSchema, SectionTypeSchemaFK, SectionTypeSchemaRel
):
    """Modelo para representar un Section."""
