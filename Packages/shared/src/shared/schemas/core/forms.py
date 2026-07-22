from pydantic import Field

from shared.schemas import (
    UUID_STR,
    DescriptionSchema,
    DisplayOrderSchema,
    HelperSchema,
    LabelSchema,
    RequiredSchema,
    UuidSchema,
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


class CardTemplateSchemaFK(CardTemplateSchema):
    """Modelo para representar un CardTemplate."""

    question_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de question.",
    )


class CardTemplateSchemaRel(CardTemplateSchema):
    """Modelo para representar un CardTemplate."""


class CardTemplateSchemaExtended(CardTemplateSchemaFK, CardTemplateSchemaRel):
    """Modelo para representar un CardTemplate."""


###############################################################################
# Field
###############################################################################


class FieldSchemaFK(FieldSchema):
    """Modelo para representar un Field."""

    form_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de formulario.",
    )
    field_group_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de field group.",
    )
    field_type_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de field type.",
    )


class FieldSchemaRel(FieldSchema):
    """Modelo para representar un Field."""


class FieldSchemaExtended(FieldSchemaFK, FieldSchemaRel):
    """Modelo para representar un Field."""


###############################################################################
# FieldChoice
###############################################################################


class FieldChoiceSchemaFK(FieldChoiceSchema):
    """Modelo para representar un FieldChoice."""

    field_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de field.",
    )


class FieldChoiceSchemaRel(FieldChoiceSchema):
    """Modelo para representar un FieldChoice."""


class FieldChoiceSchemaExtended(FieldChoiceSchemaFK, FieldChoiceSchemaRel):
    """Modelo para representar un FieldChoice."""


###############################################################################
# FieldGroup
###############################################################################


class FieldGroupSchemaFK(FieldGroupSchema):
    """Modelo para representar un FieldGroup."""

    form_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de form.",
    )
    question_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de question.",
    )
    card_template_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de card_template.",
    )


class FieldGroupSchemaRel(FieldGroupSchema):
    """Modelo para representar un FieldGroup."""


class FieldGroupSchemaExtended(FieldGroupSchemaFK, FieldGroupSchemaRel):
    """Modelo para representar un FieldGroup."""


###############################################################################
# Form
###############################################################################


class FormSchemaFK(FormSchema):
    """Modelo para representar un Form."""


class FormSchemaRel(FormSchema):
    """Modelo para representar un Form."""


class FormSchemaExtended(FormSchemaFK, FormSchemaRel):
    """Modelo para representar un Form."""


###############################################################################
# Question
###############################################################################


class QuestionSchemaFK(QuestionSchema):
    """Modelo para representar un Question."""

    form_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de form.",
    )
    section_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de section.",
    )
    file_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de file.",
    )


class QuestionSchemaRel(QuestionSchema):
    """Modelo para representar un Question."""


class QuestionSchemaExtended(QuestionSchemaFK, QuestionSchemaRel):
    """Modelo para representar un Question."""


###############################################################################
# Section
###############################################################################


class SectionSchemaFK(SectionSchema):
    """Modelo para representar un Section."""

    form_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de form.",
    )
    file_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de file.",
    )
    parent_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de parent.",
    )
    section_type_id: UUID_STR | None = Field(
        default=None,
        title="ID.",
        description="Id de section type.",
    )


class SectionSchemaRel(SectionSchema):
    """Modelo para representar un Section."""


class SectionSchemaExtended(SectionSchemaFK, SectionSchemaRel):
    """Modelo para representar un Section."""


###############################################################################
# Section Type
###############################################################################


class SectionTypeSchemaFK(SectionTypeSchema):
    """Modelo para representar un Section."""


class SectionTypeSchemaRel(SectionTypeSchema):
    """Modelo para representar un Section."""


class SectionTypeSchemaExtended(SectionTypeSchemaFK, SectionTypeSchemaRel):
    """Modelo para representar un Section."""
