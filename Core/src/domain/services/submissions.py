from uuid import UUID, uuid4

from sqlalchemy import select

from shared.enums import SubmissionStatusesEnum
from shared.models import (
    CardTemplate,
    AnswerCardEntry,
    Field,
    FieldChoice,
    FieldGroup,
    FieldType,
    File,
    Question,
    Section,
    Submission,
)

from domain.factories.answer_factory import AnswerFactory
from domain.services.errors import (
    SubmissionActorMissingError,
    SubmissionAlreadySubmittedError,
    SubmissionFormNotFoundError,
    SubmissionInvalidError,
)
from infrastructure.uow.Submission import SubmissionUoW
from schemas.submissions import CardEntryAnswerIn, SubmissionItemIn


class SubmissionService:
    async def process_submission(
        self,
        user_id: UUID,
        form_id: UUID,
        items: list[SubmissionItemIn],
        uow: SubmissionUoW,
        as_draft: bool = False,
    ) -> Submission:
        """
        Valida las respuestas contra el formulario y las guarda como radicado de la
        entidad del usuario. Un borrador anterior de la misma entidad y formulario se
        reemplaza; si ya hay un envío definitivo se rechaza (409).
        """
        if await uow.forms.get_by_id(form_id) is None:
            raise SubmissionFormNotFoundError()

        actor_link = await uow.user_actor_links.get_by_user_id(user_id)
        if not actor_link:
            raise SubmissionActorMissingError()

        status_code = (
            SubmissionStatusesEnum.DRAFT.code
            if as_draft
            else SubmissionStatusesEnum.SUBMITTED.code
        )
        status = await uow.submissions.get_status_by_code(status_code)
        if not status:
            raise ValueError(f"Submission status '{status_code}' not found in database.")

        await self._validate(uow, form_id, items)

        # Un borrador previo se reemplaza; un envío definitivo no se puede pisar.
        for previous, previous_code in await uow.submissions.list_for_actor_form(
            actor_link.actor_id, form_id
        ):
            if previous_code != SubmissionStatusesEnum.DRAFT.code:
                raise SubmissionAlreadySubmittedError()
            await uow.session.delete(previous)
        await uow.session.flush()

        submission = self.build_submission(
            actor_link.actor_id, form_id, status.id, items
        )
        uow.submissions.add(submission)
        await uow.session.flush()
        return submission

    def build_submission(
        self, actor_id: UUID, form_id: UUID, status_id: UUID, items: list[SubmissionItemIn]
    ) -> Submission:
        """Arma el radicado (sin guardarlo) con sus respuestas, tarjetas y vínculos."""
        submission = Submission(actor_id=actor_id, form_id=form_id, status_id=status_id)
        # Las tarjetas hijas se insertan después de su padre (FK parent_entry_id).
        created: dict[str, AnswerCardEntry] = {}
        for item in self._parents_first(items):
            answer = AnswerFactory.create_answer(item)
            answer.submission = submission
            submission.answers.append(answer)

            if isinstance(item, CardEntryAnswerIn):
                answer.id = uuid4()
                if item.ref:
                    created[item.ref] = answer  # type: ignore[assignment]
                if item.parent_ref:
                    answer.parent_entry_id = created[item.parent_ref].id  # type: ignore[attr-defined]
                for child_item in item.answers:
                    child = AnswerFactory.create_answer(child_item)
                    child.submission = submission
                    child.card_entry = answer  # type: ignore[assignment]
                    submission.answers.append(child)
        return submission

    @staticmethod
    def _parents_first(items: list[SubmissionItemIn]) -> list[SubmissionItemIn]:
        """Ordena para que cada tarjeta venga después de la tarjeta de la que cuelga."""
        by_ref = {i.ref: i for i in items if isinstance(i, CardEntryAnswerIn) and i.ref}

        def depth(item) -> int:
            d, node, seen = 0, item, set()
            while isinstance(node, CardEntryAnswerIn) and node.parent_ref:
                if node.parent_ref in seen:
                    break
                seen.add(node.parent_ref)
                node = by_ref.get(node.parent_ref)
                d += 1
            return d

        return sorted(items, key=depth)  # sorted es estable: conserva el orden entre iguales

    # ------------------------------------------------------------------ validation

    async def _validate(
        self, uow: SubmissionUoW, form_id: UUID, items: list[SubmissionItemIn]
    ) -> None:
        """Todos los ids deben existir y pertenecer al formulario; el tipo debe coincidir."""
        session = uow.session

        flat: list = []
        card_question: dict[int, UUID] = {}  # id(item) -> question_id de su tarjeta
        for item in items:
            flat.append(item)
            if isinstance(item, CardEntryAnswerIn):
                for child in item.answers:
                    flat.append(child)
                    card_question[id(child)] = item.question_id

        field_ids = {i.field_id for i in flat}
        rows = (
            await session.execute(
                select(Field.id, FieldType.code, Question.id, CardTemplate.id)
                .join(FieldType, FieldType.id == Field.field_type_id)
                .join(FieldGroup, FieldGroup.id == Field.field_group_id)
                .join(CardTemplate, CardTemplate.id == FieldGroup.card_template_id)
                .join(Question, Question.id == CardTemplate.question_id)
                .join(Section, Section.id == Question.section_id)
                .where(Section.form_id == form_id, Field.id.in_(field_ids))
            )
        ).all()
        known = {fid: (code, qid, tid) for fid, code, qid, tid in rows}

        missing = field_ids - known.keys()
        if missing:
            raise SubmissionInvalidError(
                f"Fields not found in this form: {sorted(str(m) for m in missing)}"
            )

        choice_ids: set[UUID] = set()
        file_ids: set[UUID] = set()
        for it in flat:
            if isinstance(it, CardEntryAnswerIn):
                continue
            expected = known[it.field_id][0]
            if it.type != expected:
                raise SubmissionInvalidError(
                    f"Field {it.field_id} is '{expected}' but the answer is '{it.type}'."
                )
            qid = card_question.get(id(it))
            if qid is not None and known[it.field_id][1] != qid:
                raise SubmissionInvalidError(
                    f"Field {it.field_id} does not belong to question {qid}."
                )
            if it.type == "single_choice":
                choice_ids.add(it.value)
            elif it.type == "multi_choice":
                choice_ids.update(it.value)
            elif it.type == "file" and it.value is not None:
                file_ids.add(it.value)

        for it in flat:
            if isinstance(it, CardEntryAnswerIn):
                _, qid, tid = known[it.field_id]
                if it.question_id != qid or it.card_template_id != tid:
                    raise SubmissionInvalidError(
                        f"Card '{it.title}' does not match its question/template."
                    )

        if choice_ids:
            valid = {
                (cid, fid)
                for cid, fid in (
                    await session.execute(
                        select(FieldChoice.id, FieldChoice.field_id).where(
                            FieldChoice.id.in_(choice_ids)
                        )
                    )
                ).all()
            }
            valid_by_choice = {cid: fid for cid, fid in valid}
            for it in flat:
                chosen = (
                    [it.value]
                    if getattr(it, "type", None) == "single_choice"
                    else it.value
                    if getattr(it, "type", None) == "multi_choice"
                    else []
                )
                for cid in chosen:
                    if valid_by_choice.get(cid) != it.field_id:
                        raise SubmissionInvalidError(
                            f"Choice {cid} is not an option of field {it.field_id}."
                        )

        if file_ids:
            found = set(
                (await session.execute(select(File.id).where(File.id.in_(file_ids)))).scalars()
            )
            if file_ids - found:
                raise SubmissionInvalidError("A referenced file does not exist.")

        await self._validate_links(uow, form_id, items)

    async def _validate_links(
        self, uow: SubmissionUoW, form_id: UUID, items: list[SubmissionItemIn]
    ) -> None:
        """
        Las preguntas con pregunta origen exigen que cada tarjeta indique (`parent_ref`)
        una tarjeta del mismo envío que pertenezca a esa pregunta origen; las demás
        preguntas no pueden traer `parent_ref`. `ref` no puede repetirse.
        """
        cards = [i for i in items if isinstance(i, CardEntryAnswerIn)]
        if not cards:
            return

        refs: dict[str, CardEntryAnswerIn] = {}
        for c in cards:
            if c.ref:
                if c.ref in refs:
                    raise SubmissionInvalidError(f"Card reference '{c.ref}' is repeated.")
                refs[c.ref] = c

        sources = dict(
            (
                await uow.session.execute(
                    select(Question.id, Question.source_question_id)
                    .join(Section, Section.id == Question.section_id)
                    .where(
                        Section.form_id == form_id,
                        Question.id.in_({c.question_id for c in cards}),
                    )
                )
            ).all()
        )

        for c in cards:
            source = sources.get(c.question_id)
            if source is None:
                if c.parent_ref:
                    raise SubmissionInvalidError(
                        f"Card '{c.title}' cannot hang from another card: its question has no source question."
                    )
                continue
            parent = refs.get(c.parent_ref) if c.parent_ref else None
            if parent is None:
                raise SubmissionInvalidError(
                    f"Card '{c.title}' must reference a card (`parent_ref`) of its source question."
                )
            if parent.question_id != source:
                raise SubmissionInvalidError(
                    f"Card '{c.title}' references a card that is not from its source question."
                )
