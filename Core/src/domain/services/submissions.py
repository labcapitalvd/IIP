from typing import List, Any
from uuid import UUID

from models import Submission, Answer, AnswerCardEntry
from domain.factories.answer_factory import AnswerFactory
from infrastructure.uow.Submission import SubmissionUoW


class SubmissionService:
    def _handle_nested_card(
        self,
        parent_card: AnswerCardEntry,
        nested_data: List[dict],
        submission: Submission,
    ):
        for item_data in nested_data:
            child_answer = AnswerFactory.create_answer(data=item_data)
            child_answer.submission = submission
            child_answer.card_entry = parent_card
            submission.answers.append(child_answer)

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
            actor_id=user_id,
            form_id=form_id,
        )

        # 3. Process the list of answers recursively
        for data in answers_data:
            answer_entity = AnswerFactory.create_answer(data=data)
            answer_entity.submission = submission
            submission.answers.append(answer_entity)

            if data.get("type") == "card_entry":
                self._handle_nested_card(
                    parent_card=answer_entity,  # type: ignore
                    nested_data=data.get("answers", []),
                    submission=submission,
                )

        uow.submissions.add(submission)

        return submission
