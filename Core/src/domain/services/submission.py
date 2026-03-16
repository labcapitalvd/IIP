from typing import List, Optional, Any
from uuid import UUID

from domain import AnswerFactory

from models import (
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
    Submission,
)
from infrastructure.uow import SubmissionUoW


class SubmissionService:
    def _handle_nested_card(self, answer_entity: Answer, data: dict):
        pass

    async def process_submission(
        self,
        user_id: UUID,
        form_id: UUID,
        answers_data: List[Any],
        uow: SubmissionUoW,
    ) -> Submission:
        """
        Main business logic for creating a submission.
        """

        # 1. Create the Submission Header
        submission = Submission(
            user_id=user_id,
            form_id=form_id,
        )

        # 3. Process the list of answers recursively
        for data in answers_data:
            answer_entity = AnswerFactory.create_answer(data=data)
            submission.answers.append(answer_entity)

            if data.get("type") == "card_loop":
                self._handle_nested_card(answer_entity, data.get("answers"))

        uow.submissions.add(submission)

        return submission

