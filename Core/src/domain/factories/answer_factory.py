from datetime import date
from decimal import Decimal
from models import (
    Answer,
    AnswerBoolean,
    AnswerText,
    AnswerNumeric,
    Submission,
    AnswerCardEntry,
    AnswerDate,
    AnswerFile,
    AnswerMultiChoice,
    AnswerSingleChoice,
)


class AnswerFactory:
    @staticmethod
    def create_answer(data: dict) -> "Answer":
        field_type = data.get("type")

        base_kwargs = {
            "field_id": data.get("field_id"),
        }

        if field_type == "boolean":
            return AnswerBoolean(
                **base_kwargs,
                value=data.get("value"),
            )

        elif field_type == "card_entry":
            return AnswerCardEntry(
                **base_kwargs,
                value=bool(data.get("value")),
            )

        elif field_type == "date":
            return AnswerDate(
                **base_kwargs,
                value=data.get("value"),
            )

        elif field_type == "file":
            return AnswerFile(
                **base_kwargs,
                value=data.get("value"),
            )

        elif field_type == "multichoice":
            return AnswerMultiChoice()

        elif field_type == "numeric":
            return AnswerNumeric(
                **base_kwargs,
                value=data.get("value"),
            )

        elif field_type == "singlechoice":
            return AnswerSingleChoice()

        elif field_type == "text":
            return AnswerText(
                **base_kwargs,
                value=data.get("value"),
            )

        raise ValueError(f"Unknown type: {field_type}")
