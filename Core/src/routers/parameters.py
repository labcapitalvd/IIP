from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, status
from shared.utils import AccessContext, get_claims

from application.parameters import ParameterAppService

router = APIRouter(tags=["Parámetros"], prefix="/parameters")


def get_service() -> ParameterAppService:
    return ParameterAppService()


def _user_id(ctx: AccessContext) -> str:
    return str(get_claims(token=ctx.access_token)["sub"])


@router.get("", operation_id="list_parameter_tables", summary="Catálogo de tablas parametrizables")
async def catalog(ctx: AccessContext = Depends(), service: ParameterAppService = Depends(get_service)):
    return await service.catalog(_user_id(ctx))


@router.get("/{key}", operation_id="list_parameter_rows", summary="Registros de una tabla de parámetros")
async def list_rows(
    key: str = Path(..., max_length=50),
    ctx: AccessContext = Depends(),
    service: ParameterAppService = Depends(get_service),
):
    return await service.list_rows(_user_id(ctx), key)


@router.post(
    "/{key}", operation_id="create_parameter", status_code=status.HTTP_201_CREATED,
    summary="Crear un registro",
)
async def create(
    key: str = Path(..., max_length=50),
    data: dict[str, Any] = Body(...),
    ctx: AccessContext = Depends(),
    service: ParameterAppService = Depends(get_service),
):
    return await service.create(_user_id(ctx), key, data)


@router.put("/{key}/{row_id}", operation_id="update_parameter", summary="Actualizar un registro")
async def update(
    key: str = Path(..., max_length=50),
    row_id: UUID = Path(...),
    data: dict[str, Any] = Body(...),
    ctx: AccessContext = Depends(),
    service: ParameterAppService = Depends(get_service),
):
    return await service.update(_user_id(ctx), key, row_id, data)


@router.delete(
    "/{key}/{row_id}", operation_id="delete_parameter", status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un registro (bloqueado si está en uso)",
)
async def delete(
    key: str = Path(..., max_length=50),
    row_id: UUID = Path(...),
    ctx: AccessContext = Depends(),
    service: ParameterAppService = Depends(get_service),
):
    await service.delete(_user_id(ctx), key, row_id)
