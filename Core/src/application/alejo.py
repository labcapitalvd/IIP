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
        Maneja la transacción y validaciones.

        Args:
            form_data: Datos del formulario a crear

        Returns:
            ResponseFormCreate: Respuesta con los datos del formulario creado

        Raises:
            ValueError: Si hay errores en la validación o el año ya existe
        """
        async with FormDesignUoW() as uow:
            # Delegar la lógica de dominio al servicio
            form = await self.form_service.create_form(
                form_data=form_data,
                uow=uow,
            )

            # Commit de la transacción
            await uow.commit()

            # Retornar la respuesta
            return ResponseFormCreate(
                id=form.id,
                anno=form.anno,
                name=form.name,
                description=form.description,
            )
