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
