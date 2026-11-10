from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from shared.schemas import ResponseMessageSchema
from shared.utils import AccessContext, get_claims

from application import AssignmentAppService
from schemas.assignments import (
    RequestAssignForm,
    RequestSelectComponents,
    ResponseAssignment,
    ResponseAssignmentAdmin,
)

router = APIRouter(tags=["Asignaciones"], prefix="/forms/assignments")


def get_assignment_service() -> AssignmentAppService:
    return AssignmentAppService()


@router.get(
    "/me",
    response_model=list[ResponseAssignment],
    response_model_exclude_none=True,
    operation_id="list_my_assignments",
    summary="Formularios asignados al usuario autenticado",
)
async def list_my_assignments(
    ctx: AccessContext = Depends(),
    service: AssignmentAppService = Depends(get_assignment_service),
):
    claims = get_claims(token=ctx.access_token)
    return await service.list_for_user(user_id=UUID(claims["sub"]))


@router.get(
    "",
    response_model=list[ResponseAssignmentAdmin],
    response_model_exclude_none=True,
    operation_id="list_assignments",
    summary="Todas las asignaciones con su avance (solo admin)",
)
async def list_assignments(
    ctx: AccessContext = Depends(),
    service: AssignmentAppService = Depends(get_assignment_service),
):
    claims = get_claims(token=ctx.access_token)
    return await service.list_all(requester_id=UUID(claims["sub"]))


@router.put(
    "/{assignment_id}/components",
    response_model=ResponseMessageSchema,
    operation_id="select_assignment_components",
    summary="La entidad elige los componentes que va a responder",
)
async def select_assignment_components(
    data: RequestSelectComponents,
    assignment_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: AssignmentAppService = Depends(get_assignment_service),
):
    claims = get_claims(token=ctx.access_token)
    await service.select_components(
        user_id=UUID(claims["sub"]),
        assignment_id=assignment_id,
        component_ids=data.component_ids,
    )
    return ResponseMessageSchema(message="ok")


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_assignment",
    summary="Revocar una asignación (solo admin)",
)
async def delete_assignment(
    assignment_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: AssignmentAppService = Depends(get_assignment_service),
):
    claims = get_claims(token=ctx.access_token)
    await service.delete(requester_id=UUID(claims["sub"]), assignment_id=assignment_id)


@router.post(
    "",
    response_model=ResponseMessageSchema,
    response_model_exclude_none=True,
    operation_id="assign_form",
    status_code=status.HTTP_201_CREATED,
    summary="Asignar un formulario IIP a un usuario de entidad (solo admin)",
)
async def assign_form(
    data: RequestAssignForm,
    ctx: AccessContext = Depends(),
    service: AssignmentAppService = Depends(get_assignment_service),
):
    claims = get_claims(token=ctx.access_token)
    await service.assign(requester_id=UUID(claims["sub"]), data=data)
    return ResponseMessageSchema(message="ok")
