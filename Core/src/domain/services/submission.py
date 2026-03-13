from typing import List, Optional, Any
from uuid import UUID

from models import (
    AnswerBoolean,
    AnswerCardEntry,
    AnswerDate,
    AnswerFile,
    AnswerMultiChoice,
    AnswerNumeric,
    AnswerSingleChoice,
    AnswerText,
    MultiChoiceOptionLink,
    Submission,
)
from infrastructure.uow import SubmissionUoW


class SubmissionService:
    async def process_submission(
        self,
        user_id: UUID,
        form_id: UUID,
        answers: List[Any],
        uow: SubmissionUoW,
    ) -> Submission:
        """
        Main business logic for creating a submission.
        """

        # 1. Create the Submission Header
        submission = Submission(
            user_id=user_id,
            form_id=form_id,
            # status_id=... (fetched via uow.statuses.get_by_label... if needed)
        )

        uow.submissions.add(submission)

        # 2. Flush to generate the Submission ID (needed for foreign keys)
        await uow.session.flush()

        # 3. Process the list of answers recursively
        for answer_data in answers:
            await self._route_answer(
                submission_id=submission.id,
                data=answer_data,
                uow=uow,
            )

        return submission

    async def _route_answer(
        self,
        submission_id: UUID,
        data: Any,
        uow: SubmissionUoW,
        parent_card_entry_id: Optional[UUID] = None,
    ):
        """
        Helper to route data to the correct specific repository based on type.
        """
        # Determine how to access data (dict vs Object/DTO)
        if hasattr(data, "type"):
            field_type = data.type
            field_id = data.field_id
            value = data.value
            answers = getattr(data, "answers", [])
            card_template_id = getattr(data, "card_template_id", None)
            question_id = getattr(data, "question_id", None)
            index = getattr(data, "index", 0)
            title = getattr(data, "title", "Card Entry")
        else:
            field_type = data.get("type")
            field_id = data.get("field_id")
            value = data.get("value")
            answers = data.get("answers", [])
            card_template_id = data.get("card_template_id")
            question_id = data.get("question_id")
            index = data.get("index", 0)
            title = data.get("title", "Card Entry")

        # Handle Polymorphic Answer Types
        if field_type == "text":
            entry = AnswerText(
                submission_id=submission_id,
                field_id=field_id,
                value=value,
                card_entry_id=parent_card_entry_id,
                discriminator="AnswerText",
            )
            uow.answers_text.add(entry)

        elif field_type == "boolean":
            entry = AnswerBoolean(
                submission_id=submission_id,
                field_id=field_id,
                value=bool(value),
                card_entry_id=parent_card_entry_id,
                discriminator="AnswerBoolean",
            )
            uow.answers_boolean.add(entry)

        elif field_type == "numeric":
            entry = AnswerNumeric(
                submission_id=submission_id,
                field_id=field_id,
                value=value,
                card_entry_id=parent_card_entry_id,
                discriminator="AnswerNumeric",
            )
            uow.answers_numeric.add(entry)

        elif field_type == "date":
            entry = AnswerDate(
                submission_id=submission_id,
                field_id=field_id,
                value=value,
                card_entry_id=parent_card_entry_id,
                discriminator="AnswerDate",
            )
            uow.answers_date.add(entry)

        elif field_type == "single_choice":
            entry = AnswerSingleChoice(
                submission_id=submission_id,
                field_id=field_id,
                value_id=value,  # Assuming value is the choice UUID
                card_entry_id=parent_card_entry_id,
                discriminator="AnswerSingleChoice",
            )
            uow.answers_single_choice.add(entry)

        elif field_type == "file":
            entry = AnswerFile(
                submission_id=submission_id,
                field_id=field_id,
                value_id=value,  # Assuming value is the file UUID
                card_entry_id=parent_card_entry_id,
                discriminator="AnswerFile",
            )
            uow.answers_file.add(entry)

        elif field_type == "multi_choice":
            # 1. Create the Answer entry
            entry = AnswerMultiChoice(
                submission_id=submission_id,
                field_id=field_id,
                card_entry_id=parent_card_entry_id,
                discriminator="AnswerMultiChoice",
            )
            uow.answers_multi_choice.add(entry)
            await uow.session.flush()  # Need ID for links

            # 2. Create the links for selected options
            if value:
                for choice_id in value:
                    link = MultiChoiceOptionLink(
                        multi_choice_answer_id=entry.id,
                        choice_id=UUID(str(choice_id)),
                    )
                    uow.multichoice_links.add(link)

        elif field_type == "card_loop":
            # A Card Entry is a container for one iteration.
            entry = AnswerCardEntry(
                submission_id=submission_id,
                field_id=field_id,
                question_id=question_id,
                card_template_id=card_template_id,
                card_index=index,
                title=title,
                discriminator="AnswerCardEntry",
            )
            uow.answers_card_entry.add(entry)
            await uow.session.flush()  # Need ID for children

            # RECURSION: Process children answers inside this card
            for child_answer in answers:
                await self._route_answer(
                    submission_id=submission_id,
                    data=child_answer,
                    uow=uow,
                    parent_card_entry_id=entry.id,
                )
