from datetime import datetime
from uuid import UUID

from pydantic import Field

from shared.schemas import BaseSchema, UuidSchema


class ResponseHistoricalForm(UuidSchema):
    """Fila de la lista de formularios para las cargas históricas."""

    code: str
    label: str
    year: int | None = None
    is_active: bool
    edition_closed_at: datetime | None = Field(
        default=None, description="Fecha de cierre de la edición; sin ella no hay plantillas."
    )
    submission_count: int = Field(description="Radicados (respuestas) ya guardados.")
    result_count: int = Field(description="Entidades con resultados cargados.")


class ResponseRecord(BaseSchema):
    """Una fila del monitor: entidad × formulario, con respuestas y/o resultados cargados."""

    form_id: UUID
    form_code: str
    form_label: str
    form_year: int | None = None
    actor_id: UUID
    actor_label: str
    actor_segment_label: str | None = None
    submission_id: UUID | None = Field(default=None, description="Radicado; None si solo hay resultados.")
    status: str | None = None
    updated_at: datetime | None = None
    answer_count: int = 0
    card_count: int = 0
    has_results: bool = False
    total: float | None = Field(default=None, description="Total del resultado cargado.")


class ResponseSectionScore(BaseSchema):
    section_id: UUID
    score: float | None = None


class ResponseEntityResults(BaseSchema):
    """Resultado estadístico (el que se subió) de una entidad en un formulario."""

    has_results: bool
    total: float | None = None
    sections: list[ResponseSectionScore] = Field(default_factory=list)
    updated_at: datetime | None = None


class ResponseHistoricalIssue(BaseSchema):
    sheet: str
    row: int | None = None
    column: str | None = None
    message: str


class ResponseHistoricalReport(BaseSchema):
    """Resultado de validar/cargar un Excel. Nada se guarda si hay errores o es `dry_run`."""

    dry_run: bool
    committed: bool
    errors: list[ResponseHistoricalIssue] = Field(default_factory=list)
    warnings: list[ResponseHistoricalIssue] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
