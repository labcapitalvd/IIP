from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import with_polymorphic

from domain import SubmissionService
from domain.services.errors import (
    SubmissionForbiddenError,
    SubmissionHasGradesError,
    SubmissionNotFoundError,
)
from infrastructure.uow import SubmissionUoW
from schemas.submissions import (
    ResponseAnswerOut,
    ResponseCardOut,
    ResponseSubmissionDetail,
    ResponseSubmissionSummary,
)
from shared.db import UnitOfWork
from shared.models import (
    Actor,
    Answer,
    AnswerBoolean,
    AnswerCardEntry,
    AnswerDate,
    AnswerFile,
    AnswerMultiChoice,
    AnswerNumeric,
    AnswerSingleChoice,
    AnswerText,
    CardTemplate,
    Field,
    FieldChoice,
    FieldGroup,
    File,
    Form,
    Grade,
    MultiChoiceOptionLink,
    Question,
    Submission,
    SubmissionStatusType,
    UserActorLink,
)

from ._access import is_admin


class SubmissionAppService:
    def __init__(
        self,
        submission_service: SubmissionService | None = None,
    ):
        self.submission_service = submission_service or SubmissionService()

    async def create_submission(
        self, user_id: str, form_id: str, data: Any, as_draft: bool = False
    ):
        async with SubmissionUoW() as uow:
            submission = await self.submission_service.process_submission(
                user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                form_id=UUID(form_id) if isinstance(form_id, str) else form_id,
                items=data,
                uow=uow,
                as_draft=as_draft,
            )
            return submission

    async def delete_submission(
        self, requester_id: UUID, submission_id: UUID, force: bool = False
    ) -> None:
        """
        Borra un radicado con todas sus respuestas (solo administradores). Si ya tiene
        calificaciones responde 409 salvo que se confirme con `force`, que también las borra.
        Las respuestas, tarjetas y resultados caen por ON DELETE CASCADE; las
        calificaciones no (su FK es SET NULL sobre una columna NOT NULL), por eso se borran aquí.
        """
        async with UnitOfWork() as uow:
            session = uow.session
            if not await is_admin(session, requester_id):
                raise SubmissionForbiddenError()
            if await session.get(Submission, submission_id) is None:
                raise SubmissionNotFoundError()

            grades = await session.scalar(
                select(func.count()).select_from(Grade).where(Grade.submission_id == submission_id)
            )
            if grades and not force:
                raise SubmissionHasGradesError()
            if grades:
                await session.execute(delete(Grade).where(Grade.submission_id == submission_id))
            await session.execute(delete(Submission).where(Submission.id == submission_id))

    # ------------------------------------------------------------------ lectura

    @staticmethod
    def _summary_query():
        """Radicados con su formulario, entidad, segmento, estado y conteos."""
        counts = (
            select(
                Answer.submission_id.label("sid"),
                func.count().filter(Answer.discriminator != "card").label("answers"),
                func.count().filter(Answer.discriminator == "card").label("cards"),
            )
            .where(Answer.card_entry_id.is_(None))
            .group_by(Answer.submission_id)
            .subquery()
        )
        # Las respuestas hijas de una tarjeta también cuentan como respuestas de campo.
        children = (
            select(
                Answer.submission_id.label("sid"),
                func.count().label("n"),
            )
            .where(Answer.card_entry_id.is_not(None))
            .group_by(Answer.submission_id)
            .subquery()
        )
        return (
            select(
                Submission,
                Form,
                Actor,
                SubmissionStatusType.code,
                func.coalesce(counts.c.answers, 0) + func.coalesce(children.c.n, 0),
                func.coalesce(counts.c.cards, 0),
            )
            .join(Form, Form.id == Submission.form_id)
            .join(Actor, Actor.id == Submission.actor_id)
            .join(SubmissionStatusType, SubmissionStatusType.id == Submission.status_id)
            .outerjoin(counts, counts.c.sid == Submission.id)
            .outerjoin(children, children.c.sid == Submission.id)
        )

    @staticmethod
    def _to_summary(row, segment_label: str | None) -> dict:
        submission, form, actor, status_code, n_answers, n_cards = row
        return dict(
            id=submission.id,
            form_id=form.id,
            form_code=form.code,
            form_label=form.label,
            actor_id=actor.id,
            actor_label=actor.label,
            actor_segment_label=segment_label,
            status=status_code,
            updated_at=submission.updated_at,
            answer_count=int(n_answers),
            card_count=int(n_cards),
        )

    @staticmethod
    async def _segment_labels(session, actor_ids: set[UUID]) -> dict[UUID, str]:
        from shared.models import ActorSegment

        if not actor_ids:
            return {}
        rows = await session.execute(
            select(Actor.id, ActorSegment.label)
            .join(ActorSegment, ActorSegment.id == Actor.actor_segment_id)
            .where(Actor.id.in_(actor_ids))
        )
        return {aid: label for aid, label in rows.all()}

    @staticmethod
    async def _user_actor_id(session, user_id: UUID) -> UUID | None:
        return await session.scalar(
            select(UserActorLink.actor_id)
            .where(UserActorLink.user_id == user_id)
            .order_by(UserActorLink.updated_at.desc())
        )

    async def list_submissions(self, requester_id: UUID) -> list[ResponseSubmissionSummary]:
        """Admin: todos los radicados. Entidad: los de su entidad."""
        async with UnitOfWork() as uow:
            session = uow.session
            query = self._summary_query().order_by(Submission.updated_at.desc())
            if not await is_admin(session, requester_id):
                actor_id = await self._user_actor_id(session, requester_id)
                if actor_id is None:
                    return []
                query = query.where(Submission.actor_id == actor_id)

            rows = (await session.execute(query)).all()
            segments = await self._segment_labels(session, {r[2].id for r in rows})
            return [
                ResponseSubmissionSummary(**self._to_summary(r, segments.get(r[2].id)))
                for r in rows
            ]

    async def get_submission(
        self, requester_id: UUID, submission_id: UUID
    ) -> ResponseSubmissionDetail:
        async with UnitOfWork() as uow:
            session = uow.session
            row = (
                await session.execute(
                    self._summary_query().where(Submission.id == submission_id)
                )
            ).first()
            if row is None:
                raise SubmissionNotFoundError()

            # Una entidad solo ve lo suyo; para el resto el radicado "no existe".
            if not await is_admin(session, requester_id):
                actor_id = await self._user_actor_id(session, requester_id)
                if actor_id != row[2].id:
                    raise SubmissionNotFoundError()

            segments = await self._segment_labels(session, {row[2].id})
            summary = self._to_summary(row, segments.get(row[2].id))

            poly = with_polymorphic(Answer, "*")
            answers = (
                (
                    await session.execute(
                        select(poly).where(poly.submission_id == submission_id)
                    )
                )
                .scalars()
                .all()
            )

            field_ids = {a.field_id for a in answers}
            fields = {
                fid: (code, label, qid, qlabel)
                for fid, code, label, qid, qlabel in (
                    await session.execute(
                        select(Field.id, Field.code, Field.label, Question.id, Question.label)
                        .join(FieldGroup, FieldGroup.id == Field.field_group_id)
                        .join(CardTemplate, CardTemplate.id == FieldGroup.card_template_id)
                        .join(Question, Question.id == CardTemplate.question_id)
                        .where(Field.id.in_(field_ids))
                    )
                ).all()
            }

            multi_ids = [a.id for a in answers if isinstance(a, AnswerMultiChoice)]
            multi: dict[UUID, list[UUID]] = {}
            if multi_ids:
                for aid, cid in (
                    await session.execute(
                        select(
                            MultiChoiceOptionLink.multi_choice_answer_id,
                            MultiChoiceOptionLink.choice_id,
                        ).where(MultiChoiceOptionLink.multi_choice_answer_id.in_(multi_ids))
                    )
                ).all():
                    multi.setdefault(aid, []).append(cid)

            choice_ids = {a.value_id for a in answers if isinstance(a, AnswerSingleChoice)}
            choice_ids.update(c for cs in multi.values() for c in cs)
            choices = (
                {
                    cid: label
                    for cid, label in (
                        await session.execute(
                            select(FieldChoice.id, FieldChoice.label).where(
                                FieldChoice.id.in_(choice_ids)
                            )
                        )
                    ).all()
                }
                if choice_ids
                else {}
            )

            file_ids = {a.value_id for a in answers if isinstance(a, AnswerFile) and a.value_id}
            files = (
                {
                    fid: name
                    for fid, name in (
                        await session.execute(
                            select(File.id, File.filename).where(File.id.in_(file_ids))
                        )
                    ).all()
                }
                if file_ids
                else {}
            )

            def convert(a: Answer) -> ResponseAnswerOut:
                code, label, qid, qlabel = fields[a.field_id]
                value: Any
                display: str
                if isinstance(a, AnswerBoolean):
                    value, display = a.value, "Sí" if a.value else "No"
                elif isinstance(a, AnswerNumeric):
                    value = float(a.value) if isinstance(a.value, Decimal) else a.value
                    display = f"{a.value:f}".rstrip("0").rstrip(".") if isinstance(a.value, Decimal) else str(a.value)
                elif isinstance(a, AnswerDate):
                    value = a.value.isoformat() if isinstance(a.value, date) else a.value
                    display = str(value or "")
                elif isinstance(a, AnswerSingleChoice):
                    value, display = a.value_id, choices.get(a.value_id, "")
                elif isinstance(a, AnswerMultiChoice):
                    ids = multi.get(a.id, [])
                    value, display = ids, ", ".join(choices.get(i, "") for i in ids)
                elif isinstance(a, AnswerFile):
                    value, display = a.value_id, files.get(a.value_id, "") if a.value_id else ""
                elif isinstance(a, AnswerText):
                    value, display = a.value, a.value
                else:  # pragma: no cover - tipos futuros
                    value, display = None, ""
                return ResponseAnswerOut(
                    field_id=a.field_id,
                    field_code=code,
                    field_label=label,
                    question_id=qid,
                    question_label=qlabel,
                    type=a.discriminator,
                    value=value,
                    display=display,
                )

            top = [
                convert(a)
                for a in answers
                if a.card_entry_id is None and not isinstance(a, AnswerCardEntry)
            ]
            children: dict[UUID, list[ResponseAnswerOut]] = {}
            for a in answers:
                if a.card_entry_id is not None:
                    children.setdefault(a.card_entry_id, []).append(convert(a))

            qlabels = {v[2]: v[3] for v in fields.values()}
            cards = [
                ResponseCardOut(
                    id=a.id,
                    question_id=a.question_id,
                    question_label=qlabels.get(a.question_id, ""),
                    card_template_id=a.card_template_id,
                    title=a.title,
                    card_index=a.card_index,
                    answers=children.get(a.id, []),
                )
                for a in sorted(
                    (x for x in answers if isinstance(x, AnswerCardEntry)),
                    key=lambda x: (str(x.question_id), x.card_index),
                )
            ]
            return ResponseSubmissionDetail(**summary, answers=top, cards=cards)
