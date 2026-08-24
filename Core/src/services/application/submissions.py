from typing import Any
from uuid import UUID

from domain import SubmissionService
from infrastructure.uow import SubmissionUoW

from shared.models import Submission


class SubmissionAppService:
    def __init__(
        self,
        submission_service: SubmissionService | None = None,
    ):
        self.submission_service = submission_service or SubmissionService()

    async def create_submission(self, user_id: str, form_id: str, data: Any):
        async with SubmissionUoW() as uow:
            submission = await self.submission_service.process_submission(
                user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                form_id=UUID(form_id) if isinstance(form_id, str) else form_id,
                answers_data=data,
                uow=uow,
            )
            return submission
