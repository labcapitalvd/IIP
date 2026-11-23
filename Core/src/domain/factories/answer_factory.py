from shared.models import (
    Answer,
    AnswerBoolean,
    AnswerCardEntry,
    AnswerChoiceText,
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
            choice_texts = []
            if data.other_text and data.other_text.strip():
                choice_texts.append(
                    AnswerChoiceText(choice_id=data.value, text=data.other_text.strip())
                )
            return AnswerSingleChoice(
                field_id=data.field_id,
                value_id=data.value,
                choice_texts=choice_texts,
            )
        if isinstance(data, MultiChoiceAnswerIn):
            unique_ids = list(dict.fromkeys(data.value))
            other_texts = data.other_texts or {}
            choice_texts = [
                AnswerChoiceText(choice_id=cid, text=other_texts[cid].strip())
                for cid in unique_ids
                if other_texts.get(cid) and other_texts[cid].strip()
            ]
            return AnswerMultiChoice(
                field_id=data.field_id,
                option_links=[MultiChoiceOptionLink(choice_id=cid) for cid in unique_ids],
                choice_texts=choice_texts,
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
