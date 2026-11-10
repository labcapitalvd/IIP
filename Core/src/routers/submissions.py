from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from shared.schemas import ResponseMessageSchema
from shared.utils import AccessContext, get_claims

from application import ReopenAppService, SubmissionAppService
from schemas.submissions import (
    RequestReopen,
    RequestResolveReopen,
    ResponseReopenRequest,
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


def get_reopen_service() -> ReopenAppService:
    return ReopenAppService()


@router.get(
    "/reopen-requests",
    response_model=List[ResponseReopenRequest],
    response_model_exclude_none=True,
    operation_id="list_reopen_requests",
    summary="Solicitudes de modificación de formularios enviados (solo admin)",
)
async def list_reopen_requests(
    status_filter: str | None = Query(None, alias="status", pattern="^(pending|approved|rejected)$"),
    ctx: AccessContext = Depends(),
    service: ReopenAppService = Depends(get_reopen_service),
):
    claims = get_claims(ctx.access_token)
    return await service.list_all(requester_id=UUID(claims["sub"]), status=status_filter)


@router.post(
    "/reopen-requests/{request_id}/resolution",
    response_model=ResponseMessageSchema,
    operation_id="resolve_reopen_request",
    summary="Aprobar (el envío vuelve a borrador) o rechazar una solicitud (solo admin)",
)
async def resolve_reopen_request(
    data: RequestResolveReopen,
    request_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: ReopenAppService = Depends(get_reopen_service),
):
    claims = get_claims(ctx.access_token)
    await service.resolve(requester_id=UUID(claims["sub"]), request_id=request_id, data=data)
    return ResponseMessageSchema(message="ok")


@router.post(
    "/forms/{form_id}/reopen-requests",
    response_model=ResponseMessageSchema,
    status_code=status.HTTP_201_CREATED,
    operation_id="request_reopen",
    summary="La entidad solicita modificar un formulario ya enviado",
)
async def request_reopen(
    data: RequestReopen,
    form_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: ReopenAppService = Depends(get_reopen_service),
):
    claims = get_claims(ctx.access_token)
    await service.request(user_id=UUID(claims["sub"]), form_id=form_id, data=data)
    return ResponseMessageSchema(message="ok")


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


@router.delete(
    "/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_submission",
    summary="Eliminar un radicado y sus respuestas (solo admin)",
)
async def delete_submission(
    submission_id: UUID = Path(),
    force: bool = Query(
        False, description="true también borra sus calificaciones si las tiene (si no, 409)."
    ),
    ctx: AccessContext = Depends(),
    service: SubmissionAppService = Depends(get_submission_service),
):
    claims = get_claims(ctx.access_token)
    await service.delete_submission(
        requester_id=UUID(claims["sub"]), submission_id=submission_id, force=force
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
