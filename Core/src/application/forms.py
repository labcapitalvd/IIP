from domain import FormService
from infrastructure.uow import FormDesignUoW
from schemas.forms import CreateFormRequest, ResponseFormCreate


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
            )
