from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from shared.schemas import BaseSchema

AssignmentStatus = Literal["pending", "in_progress", "submitted"]

##############################################################################################
# Requests
##############################################################################################


class RequestAssignForm(BaseSchema):
    """Asigna un formulario a un usuario de entidad."""

    user_id: UUID = Field(description="Usuario de entidad que debe diligenciar el formulario.")
    form_id: UUID = Field(description="Formulario IIP a asignar.")
    due_date: date | None = Field(default=None, description="Fecha límite.")
    notes: str | None = Field(default=None, max_length=2048)


class RequestSelectComponents(BaseSchema):
    """Componentes del formulario que la entidad elige responder."""

    component_ids: list[UUID] = Field(min_length=1, description="Ids de los componentes elegidos.")


##############################################################################################
# Responses
##############################################################################################


class ResponseAssignment(BaseSchema):
    """Formulario asignado a un usuario, con el avance de su entidad."""

    id: UUID
    form_id: UUID
    form_code: str
    form_label: str
    form_description: str | None = None
    actor_id: UUID | None = None
    actor_label: str | None = None
    assigned_at: datetime
    due_date: date | None = None
    notes: str | None = None
    status: AssignmentStatus
    completion_percentage: int = Field(ge=0, le=100)
    submission_id: UUID | None = None
    selected_component_ids: list[UUID] | None = Field(
        default=None, description="Componentes elegidos por la entidad; null si aún no elige."
    )
    reopen_status: Literal["pending", "approved", "rejected"] | None = Field(
        default=None, description="Última solicitud de modificación de la entidad para este formulario."
    )
    reopen_note: str | None = Field(default=None, description="Nota del administrador a esa solicitud.")


class ResponseAssignmentAdmin(ResponseAssignment):
    """Asignación tal como la ve el administrador: incluye al usuario asignado."""

    user_id: UUID
    user_name: str
    user_email: str
    form_year: int | None = None
    actor_segment_label: str | None = None
