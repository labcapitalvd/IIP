from models import (
    Answer,
    AnswerBoolean,
    AnswerText,
    AnswerNumeric,
    Submission,
    AnswerCardEntry, AnswerDate, AnswerFile, AnswerMultiChoice, AnswerSingleChoice,
)


class AnswerFactory:
    @staticmethod
    def create_answer(data: dict) -> "Answer":
        field_type = data.get("type")

        if field_type == "boolean":
            return AnswerBoolean(
                field_id=data.get("field_id"),
                value=bool(data.get("value")),
                discriminator="AnswerBoolean",
            )

        elif field_type == "card_entry":
            return AnswerCardEntry()

        elif field_type == "date":
            return AnswerDate()

        elif field_type == "file":
            return AnswerFile()

        elif field_type == "multichoice":
            return AnswerMultiChoice()

        elif field_type == "numeric":
            return AnswerNumeric()

        elif field_type == "singlechoice":
            return AnswerSingleChoice()

        elif field_type == "text":
            return AnswerText()

        raise ValueError(f"Unknown type: {field_type}")
