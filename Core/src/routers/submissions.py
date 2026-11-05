from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query
from shared.utils import AccessContext, get_claims

from application import SubmissionAppService
from schemas.submissions import (
    ResponseSubmissionCreated,
    ResponseSubmissionDetail,
    ResponseSubmissionSummary,
    SubmissionItemIn,
)

router = APIRouter(tags=["Submissions"], prefix="/submissions")


def get_submission_service() -> SubmissionAppService:
    return SubmissionAppService()


@router.get(
    "",
    response_model=List[ResponseSubmissionSummary],
    response_model_exclude_none=True,
    operation_id="list_submissions",
    summary="Radicados: todos (admin) o los de la propia entidad",
)
async def list_submissions(
    ctx: AccessContext = Depends(),
    service: SubmissionAppService = Depends(get_submission_service),
):
    claims = get_claims(ctx.access_token)
    return await service.list_submissions(requester_id=UUID(claims["sub"]))


@router.get(
    "/{submission_id}",
    response_model=ResponseSubmissionDetail,
    response_model_exclude_none=True,
    operation_id="get_submission",
    summary="Detalle de un radicado con sus respuestas legibles",
)
async def get_submission(
    submission_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: SubmissionAppService = Depends(get_submission_service),
):
    claims = get_claims(ctx.access_token)
    return await service.get_submission(
        requester_id=UUID(claims["sub"]), submission_id=submission_id
    )


@router.post(
    "/forms/{form_id}",
    response_model=ResponseSubmissionCreated,
    response_model_exclude_none=True,
    operation_id="send_submission",
)
async def create_submission(
    form_id: UUID = Path(),
    answers: List[SubmissionItemIn] = Body(...),
    as_draft: bool = Query(
        False, description="true guarda un borrador (reemplaza el anterior); false radica el envío."
    ),
    ctx: AccessContext = Depends(),
    service: SubmissionAppService = Depends(get_submission_service),
):
    """
    Guarda las respuestas de la entidad del usuario para el formulario.

    Tipos de respuesta: boolean, text, numeric, date, single_choice (value = id de opción),
    multi_choice (value = lista de ids), file (value = id de archivo) y card_entry
    (tarjeta de un bucle, con sus `answers`). Se validan contra el formulario (422).
    Si la entidad ya radicó el formulario responde 409.
    """
    claims = get_claims(ctx.access_token)
    submission = await service.create_submission(
        user_id=str(claims.get("sub")),
        form_id=str(form_id),
        data=answers,
        as_draft=as_draft,
    )
    return ResponseSubmissionCreated(
        message=f"submission {form_id} created.",
        submission_id=submission.id,
        submission_status="draft" if as_draft else "submitted",
    )
