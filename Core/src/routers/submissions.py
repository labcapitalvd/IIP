from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from shared_schemas import ResponseMessage
from shared_utils import AccessContext, get_claims

from application import SubmissionAppService

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
    form_id: UUID = Query(),
    answers: List[Any] = Body(...),
    ctx: AccessContext = Depends(),
    service: SubmissionAppService = Depends(get_submission_service),
):
    user_id = get_claims(ctx.access_token)
    await service.create_submission(
        user_id=str(user_id.get("sub")), form_id=str(form_id), data=answers
    )
    return ResponseMessage(message=f"submission {form_id} created.")
