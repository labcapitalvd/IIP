from datetime import datetime, timezone
from uuid import UUID, uuid4

from shared.utils import getLogger
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from shared.models import (
    CardTemplate,
    Field,
    FieldChoice,
    FieldDependency,
    FieldGroup,
    FieldRule,
    FileType,
    Form,
    Question,
    Section,
    Submission,
)

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
    FormHasSubmissionsError,
    FormNotFoundError,
    InvalidFileFieldError,
    FormStructureConflictError,
    InvalidFieldTypeReferenceError,
    QuestionDependencyError,
    RelationalOperatorNotFoundError,
    SectionTypeNotFoundError,
)


logger = getLogger(__name__)


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

        # Explicit id so nested child sections (not reachable via form.sections)
        # can also carry `form_id`.
        pending: list = []
        form = Form(
            id=uuid4(),
            code=form_data.code,
            label=form_data.label,
            description=form_data.description,
        )

        for section_data in form_data.sections:
            form.sections.append(await self._build_section(uow, section_data, form.id, pending))

        uow.forms.add(form)

        try:
            await uow.session.flush()
            await self._create_dependencies(uow, pending)
        except IntegrityError as e:
            logger.error(f"Form creation integrity error: {e.orig}")
            raise FormStructureConflictError(
                "Could not save the form: duplicate codes within the same "
                "section/question/group, or a reference to a non-existent record."
            ) from e

        return form

    async def has_submissions(self, uow: FormDesignUoW, form_id: UUID) -> bool:
        count = await uow.session.scalar(
            select(func.count()).select_from(Submission).where(Submission.form_id == form_id)
        )
        return bool(count)

    async def get_status(self, uow: FormDesignUoW, *, code: str) -> tuple[Form, bool]:
        form = await uow.forms.get_by_code(code=code)
        if not form:
            raise FormNotFoundError(f"Form '{code}' not found in the backend.")
        return form, await self.has_submissions(uow, form.id)

    async def list_file_types(self, uow: FormDesignUoW) -> list[FileType]:
        return await uow.file_types.list_all()

    async def update_form(
        self, uow: FormDesignUoW, form_id: UUID, form_data: CreateFormRequest
    ) -> Form:
        """
        Reemplaza la estructura completa del formulario. Solo se permite mientras
        el formulario no tenga respuestas: de lo contrario se perderían o
        quedarían inconsistentes.
        """
        form = await uow.forms.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(f"Form '{form_id}' not found.")

        if await self.has_submissions(uow, form.id):
            raise FormHasSubmissionsError(
                "This form already has submissions, so it can no longer be modified."
            )

        if form_data.code != form.code:
            other = await uow.forms.get_by_code(code=form_data.code)
            if other and other.id != form.id:
                raise FormAlreadyExistsError(f"Form code '{form_data.code}' already exists.")

        # Questions reference sections with ON DELETE SET NULL, so they must go first;
        # their card templates, fields, choices, rules, dependencies and criteria cascade.
        form_sections = select(Section.id).where(Section.form_id == form.id)
        await uow.session.execute(delete(Question).where(Question.section_id.in_(form_sections)))
        await uow.session.execute(delete(Section).where(Section.form_id == form.id))

        form.code = form_data.code
        form.label = form_data.label
        form.description = form_data.description
        form.updated_at = datetime.now(timezone.utc)

        pending: list = []
        for section_data in form_data.sections:
            uow.session.add(await self._build_section(uow, section_data, form.id, pending))

        try:
            await uow.session.flush()
            await self._create_dependencies(uow, pending)
            await uow.session.flush()
        except IntegrityError as e:
            logger.error(f"Form update integrity error: {e.orig}")
            raise FormStructureConflictError(
                "Could not save the form: duplicate codes within the same "
                "section/question/group, or a reference to a non-existent record."
            ) from e

        return form

    async def _build_section(
        self, uow: FormDesignUoW, section_data: CreateSectionRequest, form_id: UUID,
        pending: list,
    ) -> Section:
        section_type = None
        if section_data.section_type_id:
            section_type = await uow.section_types.get_by_id(
                id=UUID(section_data.section_type_id)
            )
        elif section_data.section_type_code:
            section_type = await uow.section_types.get_by_code(
                code=section_data.section_type_code
            )
        if (section_data.section_type_id or section_data.section_type_code) and not section_type:
            raise SectionTypeNotFoundError(
                f"Section type '{section_data.section_type_id or section_data.section_type_code}' not found."
            )

        section = Section(
            form_id=form_id,
            code=section_data.code,
            label=section_data.label,
            description=section_data.description,
            helper=section_data.helper,
            icon=section_data.icon,
            display_order=section_data.display_order,
            type=section_type,
        )

        for child_data in section_data.children:
            section.children.append(await self._build_section(uow, child_data, form_id, pending))

        built: dict[str, Question] = {}
        for question_data in section_data.questions:
            question = await self._build_question(uow, question_data)
            section.questions.append(question)
            built[question_data.code] = question
            if question_data.depends_on:
                pending.append((question_data, question, built))

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
        if field_data.field_type_id:
            field_type = await uow.field_types.get_by_id(id=UUID(field_data.field_type_id))
        elif field_data.field_type_code:
            field_type = await uow.field_types.get_by_code(code=field_data.field_type_code)
        else:
            raise InvalidFieldTypeReferenceError(
                f"Field '{field_data.code}' needs field_type_id or field_type_code."
            )
        if not field_type:
            raise FieldTypeNotFoundError(
                f"Field type '{field_data.field_type_id or field_data.field_type_code}' not found."
            )

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

        if field_type.code == "file":
            await self._build_file_rules(uow, field, field_data)

        return field

    async def _build_file_rules(
        self, uow: FormDesignUoW, field: Field, field_data: CreateFieldRequest
    ) -> None:
        """Un campo `file` guarda sus tipos permitidos y su tamaño máximo como FieldRules."""
        codes = list(dict.fromkeys(field_data.allowed_file_type_codes))
        if not codes or not field_data.max_file_size:
            raise InvalidFileFieldError(
                f"File field '{field_data.code}' needs allowed file types and a max size."
            )
        file_types = await uow.file_types.get_by_codes(codes)
        if len(file_types) != len(codes):
            unknown = set(codes) - {t.code for t in file_types}
            raise InvalidFileFieldError(f"Unknown file types: {', '.join(sorted(unknown))}.")
        limit = int(min(t.max_size for t in file_types))
        if field_data.max_file_size > limit:
            raise InvalidFileFieldError(
                f"Max size {field_data.max_file_size} exceeds the limit of the selected types ({limit} bytes)."
            )

        for rule_code, value, message in (
            ("file_types", ",".join(codes), "Tipo de archivo no permitido."),
            ("max_file_size", str(field_data.max_file_size), "El archivo supera el tamaño máximo permitido."),
        ):
            rule_type = await uow.rule_types.get_by_code(code=rule_code)
            if not rule_type:
                raise InvalidFileFieldError(f"Rule type '{rule_code}' is not seeded.")
            field.field_rules.append(
                FieldRule(rule_type_id=rule_type.id, rule_value=value, error_message=message)
            )

    async def _create_dependencies(self, uow: FormDesignUoW, pending: list) -> None:
        """
        Crea `rules.field_dependencies` para las preguntas con `depends_on`.
        Cada campo de la tarjeta de la pregunta dependiente (p. ej. el bucle 1.1)
        queda oculto hasta que el campo Sí/No de la pregunta padre (p. ej. 1)
        tenga el valor esperado: operador `eq`, expected_value {"value": bool}.
        `pending` = [(request, question, preguntas ya construidas de su sección)].
        """
        if not pending:
            return

        operator = await uow.relational_operators.get_by_code(code="eq")
        if not operator:
            raise RelationalOperatorNotFoundError()

        for qdata, question, by_code in pending:
            dep = qdata.depends_on
            parent = by_code.get(dep.question_code)
            parent_fields = [
                f
                for g in (parent.card_template.field_groups if parent else [])
                for f in g.fields
            ]
            if (
                not parent
                or len(parent_fields) != 1
                or parent_fields[0].field_type.code != "boolean"
            ):
                raise QuestionDependencyError(
                    f"Question '{qdata.code}' depends on '{dep.question_code}', which must "
                    "be a Yes/No question of the same section."
                )
            for group in question.card_template.field_groups:
                for target in group.fields:
                    uow.session.add(
                        FieldDependency(
                            target_field_id=target.id,
                            depends_on_field_id=parent_fields[0].id,
                            relational_operator_id=operator.id,
                            expected_value={"value": dep.expected_value},
                        )
                    )

    def _build_field_choice(self, choice_data: CreateFieldChoiceRequest) -> FieldChoice:
        return FieldChoice(
            code=choice_data.code,
            label=choice_data.label,
            description=choice_data.description,
            display_order=choice_data.display_order,
        )
