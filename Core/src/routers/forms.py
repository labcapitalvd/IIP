from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from shared_utils import AccessContext, get_claims

from application.forms import FormAppService
from schemas.forms import CreateFormRequest, ResponseFormCreate

router = APIRouter(tags=["Forms"], prefix="/forms")


def get_form_service() -> FormAppService:
    return FormAppService()


def get_auth_claims(ctx: AccessContext) -> dict:
    try:
        return get_claims(ctx.access_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post(
    "",
    response_model=ResponseFormCreate,
    response_model_exclude_none=True,
    operation_id="create_form",
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo formulario",
    description="""
    Crea un nuevo formulario con su estructura jerárquica completa.
    
    ## Estructura del Formulario
    - **Form**: El contenedor principal
      - **Sections**: Secciones del formulario (pueden ser anidadas)
        - **Questions**: Preguntas dentro de cada sección
          - **FieldGroups**: Grupos de campos para cada pregunta
            - **Fields**: Campos individuales
              - **FieldChoices**: Opciones para campos de selección
    
    ## Restricciones
    - El campo `anno` (año) debe ser único
    - Al menos una sección es requerida
    - Las subsecciones se pueden anidar múltiples niveles
    - Los fields_type_id deben existir en la base de datos
    
    ## Ejemplo de Request
    ```json
    {
      "anno": 2024,
      "name": "Formulario Anual 2024",
      "description": "Descripción del formulario",
      "sections": [
        {
          "title": "Sección 1",
          "description": "Descripción de la sección",
          "display_order": 0,
          "questions": [
            {
              "title": "Pregunta 1",
              "description": "Descripción de la pregunta",
              "required": true,
              "is_loop": false,
              "display_order": 0,
              "field_groups": [
                {
                  "title": "Grupo de Campos 1",
                  "description": "Descripción del grupo",
                  "display_order": 0,
                  "fields": [
                    {
                      "title": "Campo 1",
                      "description": "Descripción del campo",
                      "required": true,
                      "field_type_id": "550e8400-e29b-41d4-a716-446655440000",
                      "display_order": 0,
                      "field_choices": [
                        {
                          "title": "Opción 1",
                          "description": "Primera opción",
                          "display_order": 0
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
    ```
    """,
)
async def create_form(
    form_data: CreateFormRequest,
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    """
    Endpoint para crear un nuevo formulario completo.
    
    Se requiere autenticación para crear formularios.
    """
    claims = get_auth_claims(ctx)
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: no se encontró identificador de usuario",
        )

    try:
        # Crear el formulario
        created_form = await service.create_form(form_data=form_data)
        return created_form

    except ValueError as e:
        # Errores de validación de negocio (ej: año duplicado)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{form_id}",
    response_model=ResponseFormCreate,
    response_model_exclude_none=True,
    operation_id="get_form",
    summary="Obtener información de un formulario",
)
async def get_form(
    form_id: str,
    ctx: AccessContext = Depends(),
    service: FormAppService = Depends(get_form_service),
):
    """
    Obtiene la información básica de un formulario por su ID.
    """
    try:
        # Validar formato de UUID
        try:
            form_uuid = UUID(form_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID de formulario inválido: {form_id}",
            )

        # Obtener el formulario
        # Aquí necesitarías implementar un método get_form en el servicio
        # Por ahora lanzamos error indicando que falta implementación
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Endpoint de lectura aún no implementado",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el formulario: {str(e)}",
        )
