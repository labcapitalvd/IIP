from datetime import date
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

##############################################################################################
# Responses
##############################################################################################


class ResponseSubmissionCreated(ResponseMessageSchema):
    submission_id: UUID
    submission_status: Literal["draft", "submitted"]
