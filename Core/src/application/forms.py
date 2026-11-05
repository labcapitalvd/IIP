from domain import FormService
from infrastructure.uow import FormDesignUoW
from uuid import UUID

from shared.models import Form, Question, Section

from schemas.forms import (
    CreateFormRequest,
    ResponseCardTemplateTree,
    ResponseFieldChoiceTree,
    ResponseFieldGroupTree,
    ResponseFieldTree,
    ResponseFileType,
    ResponseFormCreate,
    ResponseFormStatus,
    ResponseFormSummary,
    ResponseFormTree,
    ResponseQuestionDependency,
    ResponseQuestionTree,
    ResponseSectionTree,
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

    async def list_forms(self) -> list[ResponseFormSummary]:
        async with FormDesignUoW() as uow:
            return [
                _summary(form, has_submissions)
                for form, has_submissions in await self.form_service.list_forms(uow)
            ]

    async def get_form(self, form_id: UUID) -> ResponseFormTree:
        async with FormDesignUoW() as uow:
            form, has_submissions, sections = await self.form_service.get_form_tree(
                uow=uow, form_id=form_id
            )
            return ResponseFormTree(
                **_summary(form, has_submissions).model_dump(),
                sections=_section_tree(sections),
            )

    async def delete_form(self, form_id: UUID, user_id: UUID) -> None:
        async with FormDesignUoW() as uow:
            await self.form_service.delete_form(uow=uow, form_id=form_id, user_id=user_id)

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


def _summary(form: Form, has_submissions: bool) -> ResponseFormSummary:
    return ResponseFormSummary(
        id=form.id,
        code=form.code,
        label=form.label,
        description=form.description,
        year=form.year,
        version=form.version,
        is_active=form.is_active,
        updated_at=form.updated_at,
        has_submissions=has_submissions,
    )


def _by_order(items):
    return sorted(items, key=lambda i: i.display_order)


def _section_tree(sections: list[Section]) -> list[ResponseSectionTree]:
    """Anida las secciones (vienen en plano) y resuelve cada dependencia campo->pregunta."""
    question_of_field = {
        field.id: question.id
        for section in sections
        for question in section.questions
        if question.card_template
        for group in question.card_template.field_groups
        for field in group.fields
    }
    children_of: dict = {}
    for section in sections:
        children_of.setdefault(section.parent_id, []).append(section)

    def question_tree(q: Question) -> ResponseQuestionTree:
        ct = q.card_template
        fields = [f for g in ct.field_groups for f in g.fields] if ct else []
        dep = next((d for f in fields for d in f.dependencies_triggered_by_others), None)
        depends_on = None
        if dep and dep.depends_on_field_id in question_of_field:
            depends_on = ResponseQuestionDependency(
                question_id=question_of_field[dep.depends_on_field_id],
                expected_value=bool((dep.expected_value or {}).get("value", True)),
            )
        return ResponseQuestionTree(
            id=q.id,
            code=q.code,
            label=q.label,
            description=q.description,
            helper=q.helper,
            required=q.required,
            is_loop=q.is_loop,
            display_order=q.display_order,
            weight=float(sum((c.weight for c in q.criteria), 0)),
            grading_guide=next((c.description for c in q.criteria if c.description), None),
            depends_on=depends_on,
            card_template=ResponseCardTemplateTree(
                id=ct.id,
                code=ct.code,
                label=ct.label,
                description=ct.description,
                helper=ct.helper,
                field_groups=[
                    ResponseFieldGroupTree(
                        id=g.id,
                        code=g.code,
                        label=g.label,
                        description=g.description,
                        display_order=g.display_order,
                        fields=[field_tree(f) for f in _by_order(g.fields)],
                    )
                    for g in _by_order(ct.field_groups)
                ],
            )
            if ct
            else None,
        )

    def field_tree(f) -> ResponseFieldTree:
        rules = {r.rule.code: r.rule_value for r in f.field_rules if r.rule}
        max_size = rules.get("max_file_size")
        return ResponseFieldTree(
            id=f.id,
            code=f.code,
            label=f.label,
            description=f.description,
            required=f.required,
            field_type_code=f.field_type.code,
            display_order=f.display_order,
            allowed_file_type_codes=[c for c in rules.get("file_types", "").split(",") if c],
            max_file_size=int(max_size) if max_size and max_size.isdigit() else None,
            field_choices=[
                ResponseFieldChoiceTree(
                    id=c.id,
                    code=c.code,
                    label=c.label,
                    description=c.description,
                    display_order=c.display_order,
                )
                for c in _by_order(f.field_choices)
            ],
        )

    def section_tree(s: Section) -> ResponseSectionTree:
        return ResponseSectionTree(
            id=s.id,
            code=s.code,
            label=s.label,
            description=s.description,
            helper=s.helper,
            display_order=s.display_order,
            section_type_code=s.type.code if s.type else None,
            icon=s.icon,
            questions=[question_tree(q) for q in _by_order(s.questions)],
            children=[section_tree(c) for c in _by_order(children_of.get(s.id, []))],
        )

    return [section_tree(s) for s in _by_order(children_of.get(None, []))]
