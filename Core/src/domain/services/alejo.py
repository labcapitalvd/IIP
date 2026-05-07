from typing import List, Optional
from uuid import UUID

from shared_models import (
    Form,
    Section,
    Question,
    FieldGroup,
    Field,
    FieldChoice,
)
from infrastructure.uow.FormDesign import FormDesignUoW
from schemas.forms import (
    CreateFormRequest,
    CreateSectionRequest,
    CreateQuestionRequest,
    CreateFieldGroupRequest,
    CreateFieldRequest,
    CreateFieldChoiceRequest,
)


class FormService:
    """
    Domain service para la lógica de creación y gestión de formularios.
    Maneja todas las relaciones y restricciones del formulario.
    """

    async def create_form(
        self,
        form_data: CreateFormRequest,
        uow: FormDesignUoW,
    ) -> Form:
        """
        Crea un nuevo formulario completo con su estructura jerárquica.
        Valida que el año sea único y crea todas las relaciones necesarias.

        Args:
            form_data: Datos del formulario a crear
            uow: Unit of Work para persistencia

        Returns:
            Form: El formulario creado

        Raises:
            ValueError: Si el año ya existe o si hay validaciones fallidas
        """
        # Validar que el año sea único
        existing_form = await uow.forms.get_by_anno(form_data.anno)
        if existing_form:
            raise ValueError(
                f"Ya existe un formulario para el año {form_data.anno}"
            )

        # Crear el formulario base
        form = Form(
            anno=form_data.anno,
            name=form_data.name,
            description=form_data.description,
        )

        # Procesar las secciones del formulario
        for section_data in form_data.sections:
            section = await self._create_section(
                section_data=section_data,
                form=form,
                parent_section=None,
                uow=uow,
            )
            form.sections.append(section)

        # Agregar el formulario al repositorio (las relaciones en cascada se manejan automáticamente)
        uow.forms.add(form)

        return form

    async def _create_section(
        self,
        section_data: CreateSectionRequest,
        form: Form,
        parent_section: Optional[Section],
        uow: FormDesignUoW,
    ) -> Section:
        """
        Crea una sección (con soporte para subsecciones anidadas).

        Args:
            section_data: Datos de la sección
            form: Formulario padre
            parent_section: Sección padre si es una subsección
            uow: Unit of Work

        Returns:
            Section: La sección creada
        """
        section = Section(
            form_id=form.id,
            parent_id=parent_section.id if parent_section else None,
            section_type_id=(
                UUID(section_data.section_type_id)
                if section_data.section_type_id
                else None
            ),
            title=section_data.title,
            description=section_data.description,
            helper=section_data.helper,
            display_order=section_data.display_order,
        )

        # Procesar subsecciones anidadas
        for child_section_data in section_data.children or []:
            child_section = await self._create_section(
                section_data=child_section_data,
                form=form,
                parent_section=section,
                uow=uow,
            )
            section.children.append(child_section)

        # Procesar las preguntas de la sección
        for question_data in section_data.questions or []:
            question = await self._create_question(
                question_data=question_data,
                form=form,
                section=section,
                uow=uow,
            )
            section.questions.append(question)

        uow.sections.add(section)

        return section

    async def _create_question(
        self,
        question_data: CreateQuestionRequest,
        form: Form,
        section: Section,
        uow: FormDesignUoW,
    ) -> Question:
        """
        Crea una pregunta con sus grupos de campos.

        Args:
            question_data: Datos de la pregunta
            form: Formulario padre
            section: Sección padre
            uow: Unit of Work

        Returns:
            Question: La pregunta creada
        """
        question = Question(
            form_id=form.id,
            section_id=section.id,
            title=question_data.title,
            description=question_data.description,
            helper=question_data.helper,
            required=question_data.required,
            is_loop=question_data.is_loop,
            display_order=question_data.display_order,
        )

        # Procesar los grupos de campos
        for field_group_data in question_data.field_groups or []:
            field_group = await self._create_field_group(
                field_group_data=field_group_data,
                form=form,
                question=question,
                uow=uow,
            )
            question.field_groups.append(field_group)

        uow.questions.add(question)

        return question

    async def _create_field_group(
        self,
        field_group_data: CreateFieldGroupRequest,
        form: Form,
        question: Question,
        uow: FormDesignUoW,
    ) -> FieldGroup:
        """
        Crea un grupo de campos dentro de una pregunta.

        Args:
            field_group_data: Datos del grupo de campos
            form: Formulario padre
            question: Pregunta padre
            uow: Unit of Work

        Returns:
            FieldGroup: El grupo de campos creado
        """
        field_group = FieldGroup(
            form_id=form.id,
            question_id=question.id,
            title=field_group_data.title,
            description=field_group_data.description,
            display_order=field_group_data.display_order,
        )

        # Procesar los campos del grupo
        for field_data in field_group_data.fields or []:
            field = await self._create_field(
                field_data=field_data,
                form=form,
                field_group=field_group,
                uow=uow,
            )
            field_group.fields.append(field)

        uow.field_groups.add(field_group)

        return field_group

    async def _create_field(
        self,
        field_data: CreateFieldRequest,
        form: Form,
        field_group: FieldGroup,
        uow: FormDesignUoW,
    ) -> Field:
        """
        Crea un campo dentro de un grupo de campos.

        Args:
            field_data: Datos del campo
            form: Formulario padre
            field_group: Grupo de campos padre
            uow: Unit of Work

        Returns:
            Field: El campo creado
        """
        field = Field(
            form_id=form.id,
            field_group_id=field_group.id,
            field_type_id=UUID(field_data.field_type_id),
            title=field_data.title,
            description=field_data.description,
            required=field_data.required,
            display_order=field_data.display_order,
        )

        # Procesar las opciones del campo (si aplica)
        for choice_data in field_data.field_choices or []:
            choice = await self._create_field_choice(
                choice_data=choice_data,
                field=field,
                uow=uow,
            )
            field.field_choices.append(choice)

        uow.fields.add(field)

        return field

    async def _create_field_choice(
        self,
        choice_data: CreateFieldChoiceRequest,
        field: Field,
        uow: FormDesignUoW,
    ) -> FieldChoice:
        """
        Crea una opción para un campo.

        Args:
            choice_data: Datos de la opción
            field: Campo padre
            uow: Unit of Work

        Returns:
            FieldChoice: La opción creada
        """
        choice = FieldChoice(
            field_id=field.id,
            title=choice_data.title,
            description=choice_data.description,
            display_order=choice_data.display_order,
        )

        uow.field_choices.add(choice)

        return choice
