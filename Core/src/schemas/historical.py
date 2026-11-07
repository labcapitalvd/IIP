from datetime import datetime

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
