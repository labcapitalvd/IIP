from domain import FormService
from infrastructure.uow import FormDesignUoW
from uuid import UUID

from schemas.forms import (
    CreateFormRequest,
    ResponseFileType,
    ResponseFormCreate,
    ResponseFormStatus,
)


class FormAppService:
    """
    Application Service para la creación y gestión de formularios.
    Orquesta la lógica de dominio y gestiona transacciones.
    """

    def __init__(self, form_service: FormService | None = None):
        self.form_service = form_service or FormService()

    async def create_form(self, form_data: CreateFormRequest) -> ResponseFormCreate:
        """
        Crea un nuevo formulario completo con su estructura jerárquica.
        La transacción se confirma automáticamente al salir del bloque
        `async with` (ver `UnitOfWork.__aexit__`).

        Args:
            form_data: Datos del formulario a crear

        Returns:
            ResponseFormCreate: Respuesta con los datos del formulario creado
        """
        async with FormDesignUoW() as uow:
            form = await self.form_service.create_form(
                uow=uow,
                form_data=form_data,
            )

            return ResponseFormCreate(
                id=form.id,
                code=form.code,
                label=form.label,
                description=form.description,
                updated_at=form.updated_at,
            )

    async def update_form(self, form_id: UUID, form_data: CreateFormRequest) -> ResponseFormCreate:
        """Reemplaza la estructura de un formulario sin respuestas."""
        async with FormDesignUoW() as uow:
            form = await self.form_service.update_form(
                uow=uow, form_id=form_id, form_data=form_data
            )
            return ResponseFormCreate(
                id=form.id,
                code=form.code,
                label=form.label,
                description=form.description,
                updated_at=form.updated_at,
            )

    async def get_form_status(self, code: str) -> ResponseFormStatus:
        async with FormDesignUoW() as uow:
            form, has_submissions = await self.form_service.get_status(uow=uow, code=code)
            return ResponseFormStatus(
                id=form.id,
                code=form.code,
                label=form.label,
                updated_at=form.updated_at,
                has_submissions=has_submissions,
            )

    async def list_file_types(self) -> list[ResponseFileType]:
        async with FormDesignUoW() as uow:
            return [
                ResponseFileType(
                    code=t.code,
                    label=t.label,
                    extension=t.extension,
                    mime_type=t.mime_type,
                    category=t.category,
                    max_size=int(t.max_size),
                )
                for t in await self.form_service.list_file_types(uow)
            ]
