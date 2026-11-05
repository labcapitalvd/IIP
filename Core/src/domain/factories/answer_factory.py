from shared.models import (
    Answer,
    AnswerBoolean,
    AnswerCardEntry,
    AnswerDate,
    AnswerFile,
    AnswerMultiChoice,
    AnswerNumeric,
    AnswerSingleChoice,
    AnswerText,
    MultiChoiceOptionLink,
)

from schemas.submissions import (
    BooleanAnswerIn,
    CardEntryAnswerIn,
    DateAnswerIn,
    FileAnswerIn,
    MultiChoiceAnswerIn,
    NumericAnswerIn,
    SingleChoiceAnswerIn,
    TextAnswerIn,
)


class AnswerFactory:
    """Builds the polymorphic `Answer` ORM entity for an already-validated payload item."""

    @staticmethod
    def create_answer(data) -> Answer:
        if isinstance(data, BooleanAnswerIn):
            return AnswerBoolean(field_id=data.field_id, value=data.value)
        if isinstance(data, TextAnswerIn):
            return AnswerText(field_id=data.field_id, value=data.value)
        if isinstance(data, NumericAnswerIn):
            return AnswerNumeric(field_id=data.field_id, value=data.value)
        if isinstance(data, DateAnswerIn):
            return AnswerDate(field_id=data.field_id, value=data.value)
        if isinstance(data, SingleChoiceAnswerIn):
            return AnswerSingleChoice(field_id=data.field_id, value_id=data.value)
        if isinstance(data, MultiChoiceAnswerIn):
            return AnswerMultiChoice(
                field_id=data.field_id,
                option_links=[
                    MultiChoiceOptionLink(choice_id=cid) for cid in dict.fromkeys(data.value)
                ],
            )
        if isinstance(data, FileAnswerIn):
            return AnswerFile(field_id=data.field_id, value_id=data.value)
        if isinstance(data, CardEntryAnswerIn):
            return AnswerCardEntry(
                field_id=data.field_id,
                question_id=data.question_id,
                card_template_id=data.card_template_id,
                title=data.title,
                card_index=data.card_index,
            )
        raise ValueError(f"Unknown answer item: {type(data).__name__}")
