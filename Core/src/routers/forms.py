from fastapi import APIRouter, Depends, status
from shared.utils import AccessContext, get_claims

from application import FormAppService
from schemas.forms import CreateFormRequest, ResponseFormCreate

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
