from typing import Any
from uuid import UUID

from domain import SubmissionService
from infrastructure.uow import SubmissionUoW 

from models import Submission

class SubmissionAppService:
    def __init__(
        self,
        submission_service: SubmissionService | None = None,
    ):
        self.submission_service = submission_service or SubmissionService()

    async def submit_answers(self, user_id: str, data: Any) -> Submission:
        async with SubmissionUoW() as uow:
            return await self.submission_service.process_submission(
                user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                form_id=data.form_id,
                answers=data.answers,
                uow=uow
            )

