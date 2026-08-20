from typing import Annotated, Optional, List
from annotated_types import Len
from pydantic import Field

from shared.schemas import BaseSchema, UuidSchema

##############################################################################################
# Requests
##############################################################################################


class RequestForm(UuidSchema):
    """Modelo para representar una solicitud de índice."""

    detailed: bool = Field(
        False,
        description="Determinar si se desea obtener información detallada o simple.",
    )


class CreateFieldChoiceRequest(BaseSchema):
    """Modelo para crear opciones de campo (tabla `forms.field_choices`)."""

    code: str = Field(
        ..., min_length=1, max_length=50, description="Código único dentro del campo"
    )
    label: str = Field(
        ..., min_length=1, max_length=255, description="Etiqueta visible de la opción"
    )
    description: str | None = Field(
        default=None, max_length=4096, description="Descripción de la opción"
    )
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")


class CreateFieldRequest(BaseSchema):
    """Modelo para crear campos dentro de un grupo (tabla `forms.fields`)."""

    code: str = Field(
        ..., min_length=1, max_length=50, description="Código único dentro del grupo"
    )
    label: str = Field(
        ..., min_length=1, max_length=255, description="Etiqueta visible del campo"
    )
    description: str | None = Field(
        default=None, max_length=4096, description="Descripción del campo"
    )
    required: bool = Field(default=True, description="Si el campo es requerido")
    field_type_id: str = Field(
        ..., description="UUID del tipo de campo (tabla reference.field_types)"
    )
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")
    field_choices: list["CreateFieldChoiceRequest"] = Field(
        default_factory=list,
        description="Opciones del campo (solo aplica a tipos de selección)",
    )


class CreateFieldGroupRequest(BaseSchema):
    """Modelo para crear grupos de campos (tabla `forms.field_groups`)."""

    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código único dentro del card template",
    )
    label: str = Field(
        ..., min_length=1, max_length=255, description="Etiqueta visible del grupo"
    )
    description: str | None = Field(
        default=None, max_length=4096, description="Descripción del grupo"
    )
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")
    fields: list["CreateFieldRequest"] = Field(
        default_factory=list, description="Campos del grupo"
    )


class CreateCardTemplateRequest(BaseSchema):
    """
    Modelo para la plantilla de tarjeta de una pregunta (tabla `forms.card_templates`).
    Toda pregunta tiene exactamente una, se use o no `is_loop`.
    """

    code: str = Field(
        ..., min_length=1, max_length=50, description="Código único dentro de la pregunta"
    )
    label: str = Field(
        ..., min_length=1, max_length=255, description="Etiqueta visible de la tarjeta"
    )
    description: str | None = Field(
        default=None, max_length=4096, description="Descripción de la tarjeta"
    )
    helper: str | None = Field(
        default=None, description="Texto de ayuda para la tarjeta"
    )
    field_groups: list["CreateFieldGroupRequest"] = Field(
        default_factory=list, description="Grupos de campos de la tarjeta"
    )


class CreateQuestionRequest(BaseSchema):
    """Modelo para crear preguntas dentro de secciones (tabla `forms.questions`)."""

    code: str = Field(
        ..., min_length=1, max_length=50, description="Código único dentro de la sección"
    )
    label: str = Field(
        ..., min_length=1, max_length=255, description="Etiqueta visible de la pregunta"
    )
    description: str | None = Field(
        default=None, max_length=4096, description="Descripción de la pregunta"
    )
    helper: str | None = Field(None, description="Texto de ayuda para la pregunta")
    required: bool = Field(default=True, description="Si la pregunta es requerida")
    is_loop: bool = Field(
        default=False,
        description="Si la pregunta captura tarjetas repetibles (usa card_template.field_groups en bucle)",
    )
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")
    card_template: "CreateCardTemplateRequest" = Field(
        ..., description="Plantilla de tarjeta de la pregunta (obligatoria)"
    )


class CreateSectionRequest(BaseSchema):
    """Modelo para crear secciones del formulario (tabla `forms.sections`)."""

    code: str = Field(
        ..., min_length=1, max_length=50, description="Código único dentro del formulario"
    )
    label: str = Field(
        ..., min_length=1, max_length=255, description="Etiqueta visible de la sección"
    )
    description: str | None = Field(
        default=None, max_length=4096, description="Descripción de la sección"
    )
    helper: str | None = Field(None, description="Texto de ayuda para la sección")
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")
    section_type_id: str | None = Field(
        None, description="UUID del tipo de sección (tabla reference.section_types)"
    )
    questions: list["CreateQuestionRequest"] = Field(
        default_factory=list, description="Preguntas de la sección"
    )
    children: list["CreateSectionRequest"] = Field(
        default_factory=list, description="Subsecciones anidadas"
    )


CreateSectionRequest.model_rebuild()


class CreateFormRequest(BaseSchema):
    """Modelo para crear un formulario completo con su estructura (tabla `forms.forms`)."""

    code: str = Field(
        ..., min_length=1, max_length=50, description="Código único del formulario"
    )
    label: str = Field(
        ..., min_length=1, max_length=255, description="Nombre del formulario"
    )
    description: str | None = Field(
        default=None, max_length=4096, description="Descripción del formulario"
    )
    sections: list["CreateSectionRequest"] = Field(
        ..., min_length=1, description="Secciones del formulario"
    )


##############################################################################################
# Responses
##############################################################################################


class ResponseFormCreate(UuidSchema):
    """Modelo de respuesta para la creación exitosa de un formulario."""

    code: str = Field(..., description="Código del formulario")
    label: str = Field(..., description="Nombre del formulario")
    description: str | None = Field(default=None, description="Descripción del formulario")


class ResponseForm(UuidSchema):
    """Modelo para representar un formulario de forma resumida."""

    code: str = Field(..., min_length=1, max_length=50, description="Código del formulario")
    label: str | None = Field(
        None, min_length=1, max_length=512, description="Nombre del formulario"
    )
    description: str | None = Field(
        None, min_length=1, max_length=4096, description="Descripción del formulario"
    )


class ResponseForms(BaseSchema):
    """Modelo para representar una lista de formularios de forma resumida."""

    forms: Annotated[list[ResponseForm], Len(min_length=0, max_length=512)] = Field(
        ..., description="Lista de formularios"
    )
