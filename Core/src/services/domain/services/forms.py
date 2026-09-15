from uuid import UUID

from sqlalchemy.exc import IntegrityError

from shared.models import CardTemplate, Field, FieldChoice, FieldGroup, Form, Question, Section

from infrastructure.uow import FormDesignUoW
from schemas.forms import (
    CreateCardTemplateRequest,
    CreateFieldChoiceRequest,
    CreateFieldGroupRequest,
    CreateFieldRequest,
    CreateFormRequest,
    CreateQuestionRequest,
    CreateSectionRequest,
)

from .errors import (
    FieldTypeNotFoundError,
    FormAlreadyExistsError,
    FormStructureConflictError,
    SectionTypeNotFoundError,
)


class FormService:
    """
    Domain service para la creación y gestión de formularios.
    Construye el árbol Form -> Section(*) -> Question -> CardTemplate ->
    FieldGroup -> Field -> FieldChoice en memoria y deja que las relaciones de
    SQLAlchemy (cascade="save-update") persistan todo el grafo en una sola
    transacción cuando la Unit of Work hace commit.
    """

    async def create_form(self, uow: FormDesignUoW, form_data: CreateFormRequest) -> Form:
        if await uow.forms.get_by_code(code=form_data.code):
            raise FormAlreadyExistsError(f"Form code '{form_data.code}' already exists.")

        form = Form(
            code=form_data.code,
            label=form_data.label,
            description=form_data.description,
        )

        for section_data in form_data.sections:
            form.sections.append(await self._build_section(uow, section_data))

        uow.forms.add(form)

        try:
            await uow.session.flush()
        except IntegrityError as e:
            raise FormStructureConflictError(
                "Could not save the form: duplicate codes within the same "
                "section/question/group, or a reference to a non-existent record."
            ) from e

        return form

    async def _build_section(
        self, uow: FormDesignUoW, section_data: CreateSectionRequest
    ) -> Section:
        section_type = None
        if section_data.section_type_id:
            section_type = await uow.section_types.get_by_id(
                id=UUID(section_data.section_type_id)
            )
            if not section_type:
                raise SectionTypeNotFoundError(
                    f"Section type '{section_data.section_type_id}' not found."
                )

        section = Section(
            code=section_data.code,
            label=section_data.label,
            description=section_data.description,
            helper=section_data.helper,
            display_order=section_data.display_order,
            type=section_type,
        )

        for child_data in section_data.children:
            section.children.append(await self._build_section(uow, child_data))

        for question_data in section_data.questions:
            section.questions.append(await self._build_question(uow, question_data))

        return section

    async def _build_question(
        self, uow: FormDesignUoW, question_data: CreateQuestionRequest
    ) -> Question:
        question = Question(
            code=question_data.code,
            label=question_data.label,
            description=question_data.description,
            helper=question_data.helper,
            required=question_data.required,
            is_loop=question_data.is_loop,
            display_order=question_data.display_order,
        )

        question.card_template = await self._build_card_template(
            uow, question_data.card_template
        )

        return question

    async def _build_card_template(
        self, uow: FormDesignUoW, card_data: CreateCardTemplateRequest
    ) -> CardTemplate:
        card_template = CardTemplate(
            code=card_data.code,
            label=card_data.label,
            description=card_data.description,
            helper=card_data.helper,
        )

        for group_data in card_data.field_groups:
            card_template.field_groups.append(
                await self._build_field_group(uow, group_data)
            )

        return card_template

    async def _build_field_group(
        self, uow: FormDesignUoW, group_data: CreateFieldGroupRequest
    ) -> FieldGroup:
        field_group = FieldGroup(
            code=group_data.code,
            label=group_data.label,
            description=group_data.description,
            display_order=group_data.display_order,
        )

        for field_data in group_data.fields:
            field_group.fields.append(await self._build_field(uow, field_data))

        return field_group

    async def _build_field(self, uow: FormDesignUoW, field_data: CreateFieldRequest) -> Field:
        field_type = await uow.field_types.get_by_id(id=UUID(field_data.field_type_id))
        if not field_type:
            raise FieldTypeNotFoundError(f"Field type '{field_data.field_type_id}' not found.")

        field = Field(
            code=field_data.code,
            label=field_data.label,
            description=field_data.description,
            required=field_data.required,
            display_order=field_data.display_order,
            field_type=field_type,
        )

        for choice_data in field_data.field_choices:
            field.field_choices.append(self._build_field_choice(choice_data))

        return field

    def _build_field_choice(self, choice_data: CreateFieldChoiceRequest) -> FieldChoice:
        return FieldChoice(
            code=choice_data.code,
            label=choice_data.label,
            description=choice_data.description,
            display_order=choice_data.display_order,
        )
