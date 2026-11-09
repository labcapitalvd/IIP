from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select

from shared.db import UnitOfWork
from shared.enums import SubmissionStatusesEnum
from shared.models import (
    Actor,
    Form,
    Grade,
    Submission,
    SubmissionReopenRequest,
    SubmissionStatusType,
    User,
    UserActorLink,
)

from domain.services.errors import (
    ReopenAlreadyPendingError,
    ReopenAlreadyResolvedError,
    ReopenForbiddenError,
    ReopenNotAllowedError,
    ReopenRequestNotFoundError,
    SubmissionActorMissingError,
    SubmissionHasGradesError,
)
from ._access import is_admin
from schemas.submissions import RequestReopen, RequestResolveReopen, ResponseReopenRequest


class ReopenAppService:
    """Solicitud (entidad) y aprobación (administrador) para modificar un formulario ya enviado."""

    @staticmethod
    async def _submitted(session, actor_id: UUID, form_id: UUID) -> Submission | None:
        return await session.scalar(
            select(Submission)
            .join(SubmissionStatusType, SubmissionStatusType.id == Submission.status_id)
            .where(
                Submission.actor_id == actor_id,
                Submission.form_id == form_id,
                SubmissionStatusType.code == SubmissionStatusesEnum.SUBMITTED.code,
            )
        )

    async def request(self, user_id: UUID, form_id: UUID, data: RequestReopen) -> UUID:
        async with UnitOfWork() as uow:
            session = uow.session
            actor_id = await session.scalar(
                select(UserActorLink.actor_id)
                .where(UserActorLink.user_id == user_id)
                .order_by(UserActorLink.updated_at.desc())
            )
            if actor_id is None:
                raise SubmissionActorMissingError()
            if await self._submitted(session, actor_id, form_id) is None:
                raise ReopenNotAllowedError()
            pending = await session.scalar(
                select(func.count())
                .select_from(SubmissionReopenRequest)
                .where(
                    SubmissionReopenRequest.actor_id == actor_id,
                    SubmissionReopenRequest.form_id == form_id,
                    SubmissionReopenRequest.status == "pending",
                )
            )
            if pending:
                raise ReopenAlreadyPendingError()

            req = SubmissionReopenRequest(
                actor_id=actor_id,
                form_id=form_id,
                requested_by_id=user_id,
                reason=data.reason.strip(),
                status="pending",
            )
            session.add(req)
            await session.flush()
            return req.id

    async def list_all(
        self, requester_id: UUID, status: str | None = None
    ) -> list[ResponseReopenRequest]:
        async with UnitOfWork() as uow:
            session = uow.session
            if not await is_admin(session, requester_id):
                raise ReopenForbiddenError()
            query = (
                select(SubmissionReopenRequest, Form, Actor, User.username)
                .join(Form, Form.id == SubmissionReopenRequest.form_id)
                .join(Actor, Actor.id == SubmissionReopenRequest.actor_id)
                .outerjoin(User, User.id == SubmissionReopenRequest.requested_by_id)
                .order_by(SubmissionReopenRequest.requested_at.desc())
            )
            if status:
                query = query.where(SubmissionReopenRequest.status == status)
            rows = (await session.execute(query)).all()
            return [
                ResponseReopenRequest(
                    id=r.id,
                    form_id=form.id,
                    form_code=form.code,
                    form_label=form.label,
                    actor_id=actor.id,
                    actor_label=actor.label,
                    requested_by_name=username,
                    reason=r.reason,
                    status=r.status,
                    requested_at=r.requested_at,
                    resolved_at=r.resolved_at,
                    resolution_note=r.resolution_note,
                )
                for r, form, actor, username in rows
            ]

    async def resolve(
        self, requester_id: UUID, request_id: UUID, data: RequestResolveReopen
    ) -> None:
        async with UnitOfWork() as uow:
            session = uow.session
            if not await is_admin(session, requester_id):
                raise ReopenForbiddenError()
            req = await session.get(SubmissionReopenRequest, request_id)
            if req is None:
                raise ReopenRequestNotFoundError()
            if req.status != "pending":
                raise ReopenAlreadyResolvedError()

            if data.approve:
                submission = await self._submitted(session, req.actor_id, req.form_id)
                if submission is None:
                    raise ReopenNotAllowedError()
                # Guardar el borrador reemplaza el radicado: con calificaciones eso rompería su FK.
                graded = await session.scalar(
                    select(func.count()).select_from(Grade).where(Grade.submission_id == submission.id)
                )
                if graded:
                    raise SubmissionHasGradesError()
                draft_id = await session.scalar(
                    select(SubmissionStatusType.id).where(
                        SubmissionStatusType.code == SubmissionStatusesEnum.DRAFT.code
                    )
                )
                submission.status_id = draft_id

            req.status = "approved" if data.approve else "rejected"
            req.resolved_by_id = requester_id
            req.resolved_at = datetime.now(timezone.utc)
            req.resolution_note = (data.note or "").strip() or None
