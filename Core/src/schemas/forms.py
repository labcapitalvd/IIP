from typing import Annotated, Optional, List
from annotated_types import Len
from pydantic import Field, validator

from shared_schemas import BaseSchema, UuidSchema

##############################################################################################
# Requests
##############################################################################################


class RequestForm(UuidSchema):
    """Modelo para representar una solicitud de índice."""
    detailed: bool = Field(
        False, description="Determinar si se desea obtener información detallada o simple."
    )


class CreateFieldChoiceRequest(BaseSchema):
    """Modelo para crear opciones de campo."""
    title: str = Field(..., min_length=1, max_length=255, description="Título de la opción")
    description: str = Field(..., min_length=1, max_length=255, description="Descripción de la opción")
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")


class CreateFieldRequest(BaseSchema):
    """Modelo para crear campos dentro de grupos."""
    title: str = Field(..., min_length=1, max_length=255, description="Título del campo")
    description: str = Field(..., min_length=1, max_length=4096, description="Descripción del campo")
    required: bool = Field(default=True, description="Si el campo es requerido")
    field_type_id: str = Field(..., description="ID del tipo de campo (UUID)")
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")
    field_choices: Optional[List[CreateFieldChoiceRequest]] = Field(
        default_factory=list, description="Opciones del campo si aplica"
    )


class CreateFieldGroupRequest(BaseSchema):
    """Modelo para crear grupos de campos."""
    title: str = Field(..., min_length=1, max_length=255, description="Título del grupo")
    description: str = Field(..., min_length=1, max_length=4096, description="Descripción del grupo")
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")
    fields: Optional[List[CreateFieldRequest]] = Field(
        default_factory=list, description="Campos del grupo"
    )


class CreateQuestionRequest(BaseSchema):
    """Modelo para crear preguntas dentro de secciones."""
    title: str = Field(..., min_length=1, max_length=255, description="Título de la pregunta")
    description: str = Field(..., min_length=1, max_length=4096, description="Descripción de la pregunta")
    helper: Optional[str] = Field(None, description="Texto de ayuda para la pregunta")
    required: bool = Field(default=True, description="Si la pregunta es requerida")
    is_loop: bool = Field(default=False, description="Si la pregunta permite múltiples respuestas")
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")
    field_groups: Optional[List[CreateFieldGroupRequest]] = Field(
        default_factory=list, description="Grupos de campos de la pregunta"
    )


class CreateSectionRequest(BaseSchema):
    """Modelo para crear secciones del formulario."""
    title: str = Field(..., min_length=1, max_length=255, description="Título de la sección")
    description: str = Field(..., min_length=1, max_length=4096, description="Descripción de la sección")
    helper: Optional[str] = Field(None, description="Texto de ayuda para la sección")
    display_order: int = Field(default=0, ge=0, description="Orden de visualización")
    section_type_id: Optional[str] = Field(None, description="ID del tipo de sección (UUID)")
    questions: Optional[List[CreateQuestionRequest]] = Field(
        default_factory=list, description="Preguntas de la sección"
    )
    children: Optional[List["CreateSectionRequest"]] = Field(
        default_factory=list, description="Subsecciones anidadas"
    )


CreateSectionRequest.model_rebuild()


class CreateFormRequest(BaseSchema):
    """Modelo para crear un formulario completo con su estructura."""
    anno: int = Field(..., ge=1900, le=2100, description="Año del formulario (debe ser único)")
    name: str = Field(..., min_length=1, max_length=512, description="Nombre del formulario")
    description: str = Field(..., min_length=1, max_length=4096, description="Descripción del formulario")
    sections: List[CreateSectionRequest] = Field(
        ..., min_length=1, description="Secciones del formulario"
    )

    @validator("sections")
    def validate_sections(cls, v):
        if not v:
            raise ValueError("Al menos una sección es requerida")
        return v


##############################################################################################
# Responses
##############################################################################################


class ResponseFormCreate(UuidSchema):
    """Modelo de respuesta para la creación exitosa de un formulario."""
    anno: int = Field(..., description="Año del formulario")
    name: str = Field(..., description="Nombre del formulario")
    description: str = Field(..., description="Descripción del formulario")


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
