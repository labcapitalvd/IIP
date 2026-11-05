from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from shared.utils import AccessContext, get_claims

from application import FormAppService
from schemas.forms import (
    CreateFormRequest,
    ResponseFileType,
    ResponseFormCreate,
    ResponseFormStatus,
    ResponseFormSummary,
    ResponseFormTree,
)

router = APIRouter(tags=["Forms"], prefix="/forms")


def get_form_service() -> FormAppService:
    return FormAppService()


@router.post(
    "",
    response_model=ResponseFormCreate,
    response_model_exclude_none=True,
    operation_id="create_form",
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo formulario",
    description="""
    Crea un nuevo formulario con su estructura jerárquica completa en una sola
    petición, reflejando el esquema relacional de `forms.*`.

    ## Estructura del Formulario
    - **Form**: el contenedor principal (`code`, `label`, `description`)
      - **Sections**: secciones del formulario, se pueden anidar vía `children`
        - **Questions**: preguntas dentro de cada sección
          - **CardTemplate**: obligatoria en toda pregunta (una sola)
            - **FieldGroups**: grupos de campos de la tarjeta
              - **Fields**: campos individuales (requieren `field_type_id` válido)
                - **FieldChoices**: opciones, solo relevante para campos de selección

    ## Restricciones
    - `code` del formulario debe ser único en el sistema.
    - `code` debe ser único dentro de su contenedor directo (sección dentro del
      formulario, pregunta dentro de la sección, grupo dentro de la tarjeta,
      campo dentro del grupo, opción dentro del campo).
    - Se requiere al menos una sección.
    - Cada `field.field_type_id` debe existir en `reference.field_types`.
    - `section.section_type_id`, si se envía, debe existir en `reference.section_types`.
    """,
)
async def create_form(
    form_data: CreateFormRequest,
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    """Crea un formulario completo. Requiere un access token válido."""
    get_claims(token=ctx.access_token)
    return await service.create_form(form_data=form_data)


@router.get(
    "/file-types",
    response_model=list[ResponseFileType],
    operation_id="list_file_types",
    summary="Tipos de archivo disponibles para campos `file`",
)
async def list_file_types(
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    get_claims(token=ctx.access_token)
    return await service.list_file_types()


@router.get(
    "/lookup/{code}",
    response_model=ResponseFormStatus,
    operation_id="get_form_status",
    summary="Estado de un formulario por código",
    description="Devuelve el id, la fecha de última actualización y si el formulario ya tiene respuestas.",
)
async def get_form_status(
    code: str = Path(..., min_length=1, max_length=50),
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    get_claims(token=ctx.access_token)
    return await service.get_form_status(code=code)


@router.get(
    "",
    response_model=list[ResponseFormSummary],
    operation_id="list_forms",
    summary="Lista de formularios",
    description="Todos los formularios guardados en el backend, más recientes primero.",
)
async def list_forms(
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    get_claims(token=ctx.access_token)
    return await service.list_forms()


@router.get(
    "/{form_id}",
    response_model=ResponseFormTree,
    operation_id="get_form",
    summary="Formulario completo",
    description="Árbol completo del formulario (mismo formato que la creación, con ids).",
)
async def get_form(
    form_id: UUID = Path(...),
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    get_claims(token=ctx.access_token)
    return await service.get_form(form_id=form_id)


@router.delete(
    "/{form_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_form",
    summary="Eliminar un formulario",
    description="""
    Solo administradores. Se rechaza con 409 `FORM_HAS_SUBMISSIONS_ERROR` si el
    formulario ya tiene respuestas. Sus asignaciones se eliminan en cascada.
    """,
)
async def delete_form(
    form_id: UUID = Path(...),
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    claims = get_claims(token=ctx.access_token)
    await service.delete_form(form_id=form_id, user_id=UUID(str(claims["sub"])))


@router.put(
    "/{form_id}",
    response_model=ResponseFormCreate,
    response_model_exclude_none=True,
    operation_id="update_form",
    summary="Actualizar un formulario",
    description="""
    Reemplaza la estructura completa del formulario (mismo cuerpo que la creación).

    **Regla:** si el formulario ya tiene respuestas (submissions) se rechaza con
    409 `FORM_HAS_SUBMISSIONS_ERROR` y no se modifica nada.
    """,
)
async def update_form(
    form_data: CreateFormRequest,
    form_id: UUID = Path(...),
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    get_claims(token=ctx.access_token)
    return await service.update_form(form_id=form_id, form_data=form_data)
