from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from shared.db import UnitOfWork
from shared.enums import SystemRolesEnum
from shared.models import (
    Actor,
    Form,
    Submission,
    SubmissionStatusType,
    User,
    UserActorLink,
    UserFormAssignment,
    UserSystemRoleLink,
)

from domain.services.errors import (
    AssignmentForbiddenError,
    AssignmentTargetNotFoundError,
)
from schemas.assignments import RequestAssignForm, ResponseAssignment

# Porcentaje mostrado según el estado del radicado de la entidad para ese formulario.
_DRAFT_PROGRESS = 50


class AssignmentAppService:
    """Asignación de formularios IIP a usuarios de entidad y consulta de lo asignado."""

    async def assign(self, requester_id: UUID, data: RequestAssignForm) -> None:
        async with UnitOfWork() as uow:
            session = uow.session
            is_admin = await session.scalar(
                select(UserSystemRoleLink.id)
                .join(UserSystemRoleLink.system_role)
                .where(
                    UserSystemRoleLink.user_id == requester_id,
                    UserSystemRoleLink.system_role.has(
                        code=SystemRolesEnum.PLATFORM_ADMIN.code
                    ),
                )
            )
            if not is_admin:
                raise AssignmentForbiddenError()

            if not await session.get(User, data.user_id):
                raise AssignmentTargetNotFoundError()
            if not await session.get(Form, data.form_id):
                raise AssignmentTargetNotFoundError()

            existing = await session.scalar(
                select(UserFormAssignment).where(
                    UserFormAssignment.user_id == data.user_id,
                    UserFormAssignment.form_id == data.form_id,
                )
            )
            if existing:
                existing.due_date = data.due_date
                existing.notes = data.notes
            else:
                session.add(
                    UserFormAssignment(
                        user_id=data.user_id,
                        form_id=data.form_id,
                        due_date=data.due_date,
                        notes=data.notes,
                    )
                )

    async def list_for_user(self, user_id: UUID) -> list[ResponseAssignment]:
        async with UnitOfWork() as uow:
            session = uow.session

            link = await session.scalar(
                select(UserActorLink)
                .options(joinedload(UserActorLink.actor))
                .where(UserActorLink.user_id == user_id)
            )
            actor: Actor | None = link.actor if link else None

            rows = (
                await session.execute(
                    select(UserFormAssignment, Form)
                    .join(Form, Form.id == UserFormAssignment.form_id)
                    .where(UserFormAssignment.user_id == user_id)
                    .order_by(UserFormAssignment.assigned_at.desc())
                )
            ).all()

            result: list[ResponseAssignment] = []
            for assignment, form in rows:
                submission = None
                status_code = None
                if actor:
                    submission = await session.scalar(
                        select(Submission)
                        .where(
                            Submission.actor_id == actor.id,
                            Submission.form_id == form.id,
                        )
                        .order_by(Submission.updated_at.desc())
                    )
                    if submission:
                        status_code = await session.scalar(
                            select(SubmissionStatusType.code).where(
                                SubmissionStatusType.id == submission.status_id
                            )
                        )

                if submission is None:
                    status, pct = "pending", 0
                elif status_code == "draft":
                    status, pct = "in_progress", _DRAFT_PROGRESS
                else:
                    status, pct = "submitted", 100

                result.append(
                    ResponseAssignment(
                        id=assignment.id,
                        form_id=form.id,
                        form_code=form.code,
                        form_label=form.label,
                        form_description=form.description,
                        actor_id=actor.id if actor else None,
                        actor_label=actor.label if actor else None,
                        assigned_at=assignment.assigned_at,
                        due_date=assignment.due_date,
                        notes=assignment.notes,
                        status=status,
                        completion_percentage=pct,
                        submission_id=submission.id if submission else None,
                    )
                )
            return result
