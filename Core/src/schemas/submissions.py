from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Union
from uuid import UUID

from pydantic import BeforeValidator, Field

from shared.schemas import BaseSchema, ResponseMessageSchema

##############################################################################################
# Requests
##############################################################################################

# Códigos canónicos = `reference.field_types.code`. El frontend histórico enviaba
# "singlechoice" / "multichoice"; se siguen aceptando como alias.
_TYPE_ALIASES = {"singlechoice": "single_choice", "multichoice": "multi_choice"}


def _normalize_type(value: Any) -> Any:
    if isinstance(value, dict):
        t = value.get("type")
        if isinstance(t, str) and t in _TYPE_ALIASES:
            return {**value, "type": _TYPE_ALIASES[t]}
    return value


class _AnswerIn(BaseSchema):
    field_id: UUID = Field(description="Campo del formulario que se responde.")


class BooleanAnswerIn(_AnswerIn):
    type: Literal["boolean"]
    value: bool


class TextAnswerIn(_AnswerIn):
    type: Literal["text"]
    value: str


class NumericAnswerIn(_AnswerIn):
    type: Literal["numeric"]
    value: Decimal


class DateAnswerIn(_AnswerIn):
    type: Literal["date"]
    value: date


class SingleChoiceAnswerIn(_AnswerIn):
    type: Literal["single_choice"]
    value: UUID = Field(description="Id de la opción (`field_choice`) elegida.")


class MultiChoiceAnswerIn(_AnswerIn):
    type: Literal["multi_choice"]
    value: list[UUID] = Field(description="Ids de las opciones (`field_choice`) marcadas.")


class FileAnswerIn(_AnswerIn):
    type: Literal["file"]
    value: UUID | None = Field(
        default=None, description="Id del archivo ya subido (`files.files`)."
    )


ValueAnswerIn = Annotated[
    Union[
        BooleanAnswerIn,
        TextAnswerIn,
        NumericAnswerIn,
        DateAnswerIn,
        SingleChoiceAnswerIn,
        MultiChoiceAnswerIn,
        FileAnswerIn,
    ],
    Field(discriminator="type"),
]


class CardEntryAnswerIn(_AnswerIn):
    """Una tarjeta de un bucle, con las respuestas de sus campos."""

    type: Literal["card_entry"]
    question_id: UUID
    card_template_id: UUID
    title: str = Field(min_length=1, max_length=255)
    card_index: int = Field(default=0, ge=0)
    ref: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Identificador temporal (elegido por el cliente) de esta tarjeta dentro del envío.",
    )
    parent_ref: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="`ref` de la tarjeta (de la pregunta origen) de la que cuelga esta. "
        "Obligatorio si la pregunta tiene pregunta origen; prohibido si no la tiene.",
    )
    answers: list[
        Annotated[ValueAnswerIn, BeforeValidator(_normalize_type)]
    ] = Field(default_factory=list)


SubmissionItemIn = Annotated[
    Union[
        BooleanAnswerIn,
        TextAnswerIn,
        NumericAnswerIn,
        DateAnswerIn,
        SingleChoiceAnswerIn,
        MultiChoiceAnswerIn,
        FileAnswerIn,
        CardEntryAnswerIn,
    ],
    Field(discriminator="type"),
    BeforeValidator(_normalize_type),
]

class RequestReopen(BaseSchema):
    """La entidad pide modificar un formulario ya enviado."""

    reason: str = Field(min_length=10, max_length=2000, description="Motivo de la modificación.")


class RequestResolveReopen(BaseSchema):
    """El administrador aprueba o rechaza la solicitud."""

    approve: bool
    note: str | None = Field(default=None, max_length=2000)


##############################################################################################
# Responses
##############################################################################################


class ResponseSubmissionCreated(ResponseMessageSchema):
    submission_id: UUID
    submission_status: Literal["draft", "submitted"]


class ResponseSubmissionSummary(BaseSchema):
    """Fila de la lista de radicados."""

    id: UUID
    form_id: UUID
    form_code: str
    form_label: str
    actor_id: UUID
    actor_label: str
    actor_segment_label: str | None = None
    status: str = Field(description="Código de `reference.submission_status_types`.")
    updated_at: datetime
    answer_count: int = Field(description="Respuestas de campos (sin contar tarjetas).")
    card_count: int = Field(description="Tarjetas (iniciativas) de preguntas en bucle.")


class ResponseAnswerOut(BaseSchema):
    field_id: UUID
    field_code: str
    field_label: str
    question_id: UUID
    question_label: str
    type: str
    value: Any = Field(
        default=None,
        description="Valor crudo: bool, str, número, fecha ISO, id de opción, lista de ids o id de archivo.",
    )
    display: str = Field(description="Valor legible (etiqueta de la opción, nombre del archivo, Sí/No…).")


class ResponseCardOut(BaseSchema):
    id: UUID
    question_id: UUID
    question_label: str
    card_template_id: UUID
    title: str
    card_index: int
    parent_id: UUID | None = Field(
        default=None, description="Tarjeta de la pregunta origen de la que cuelga."
    )
    parent_title: str | None = Field(
        default=None, description="Nombre de la tarjeta de la que cuelga (referencia)."
    )
    answers: list[ResponseAnswerOut]


class ResponseSubmissionDetail(ResponseSubmissionSummary):
    answers: list[ResponseAnswerOut]
    cards: list[ResponseCardOut]


ReopenStatus = Literal["pending", "approved", "rejected"]


class ResponseReopenRequest(BaseSchema):
    id: UUID
    form_id: UUID
    form_code: str
    form_label: str
    actor_id: UUID
    actor_label: str
    requested_by_name: str | None = None
    reason: str
    status: ReopenStatus
    requested_at: datetime
    resolved_at: datetime | None = None
    resolution_note: str | None = None
