from uuid_utils import uuid7
from typing import List, Any

from fastapi import APIRouter, Depends, Body

from shared_utils import AccessContext


from uuid import UUID

from application import SubmissionAppService

from shared_schemas import ResponseMessage

router = APIRouter(tags=["Submissions"], prefix="/submissions")


def get_submission_service() -> SubmissionAppService:
    return SubmissionAppService()


@router.post(
    "/forms/{form_id}/submissions",
    response_model=ResponseMessage,
    response_model_exclude_none=True,
    operation_id="send_submission",
)
async def create_submission(
    form_id: UUID,
    answers: List[Any] = Body(...),
    ctx: AccessContext = Depends(),
    service: SubmissionAppService = Depends(get_submission_service)
):
    user_id = uuid7()
    await service.create_submission(
        user_id=str(user_id), form_id=str(form_id), data=answers
    )
    return ResponseMessage(message=f"submission {form_id} created.")
