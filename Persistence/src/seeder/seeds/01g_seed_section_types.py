"""Poblado de tipos de sección (Componente / Variable / Indicador)"""

from shared.db import SessionSync
from shared.models import SectionType
from shared.utils.logger import getLogger
from sqlalchemy import select

logger = getLogger(__name__)

SECTION_TYPES = [
    ("C", "COMPONENTE", "Nivel principal de organización del formulario."),
    ("V", "VARIABLE", "Agrupa indicadores relacionados dentro del formulario."),
    ("I", "INDICADOR", "Elemento concreto que se mide mediante una o varias preguntas."),
]


def upgrade() -> None:
    with SessionSync() as session:
        existing = set(session.scalars(select(SectionType.code)).all())
        new_records = [
            SectionType(code=code, label=label, description=description)
            for code, label, description in SECTION_TYPES
            if code not in existing
        ]
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.debug(
        f"SectionType seed complete: {len(new_records)} added, "
        f"{len(SECTION_TYPES) - len(new_records)} skipped."
    )
