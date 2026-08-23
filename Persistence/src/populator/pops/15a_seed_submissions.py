"""
Poblado de forms.submissions y forms.answers.

Carga las entregas (submissions) y respuestas (answers) del IIP procesando
los archivos de resultados (resultados 2019.xlsx, resultados 2021.xlsx, etc.)
ubicados en el mismo directorio del archivo de estructura IIP.

Estructura de base de datos objetivo:
  - forms.submissions (id, actor_id, form_id, status_id, created_at, updated_at)
  - forms.answers (id, submission_id, question_id, value_numeric, value_text, created_at, updated_at)

Reglas técnicas:
- Genera IDs con UUIDv7 para nuevos registros.
- Mantiene idempotencia mediante búsquedas por combinación (actor_id, form_id)
  y cláusula ON CONFLICT (submission_id, question_id) para respuestas.
- Si ya existe un registro pero su ID no es UUIDv7, detiene la ejecución para evitar inconsistencias.
- Provee la función upgrade() sin argumentos e incluye el bloque
  if __name__ == "__main__": asyncio.run(upgrade()).
"""

import asyncio
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from uuid_utils import uuid7

from shared.enums import SubmissionStatusesEnum
from shared.infrastructure import async_engine
from shared.models.targets import TargetTable
from shared.utils.logger import get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE RUTAS Y HERMANOS
# -----------------------------------------------------------------------------

LOCAL_IIP_STRUCTURE_FILE = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

# Directorio donde residen la estructura y los archivos hermanos de resultados
BASE_DIR = Path(LOCAL_IIP_STRUCTURE_FILE).parent

# Años de las encuestas / formularios a procesar
YEARS = [2019, 2021, 2023, 2025]


# -----------------------------------------------------------------------------
# UTILIDADES DE UUID
# -----------------------------------------------------------------------------


def new_uuidv7() -> str:
    """Genera un UUID versión 7 en formato string."""
    return str(uuid7())


def is_uuidv7(value: Any) -> bool:
    """Valida si un valor es un UUIDv7 válido."""
    if value is None:
        return False
    try:
        parsed = UUID(str(value))
        return parsed.version == 7
    except Exception:
        return False


# -----------------------------------------------------------------------------
# CONSULTAS A LA BASE DE DATOS
# -----------------------------------------------------------------------------


async def get_actor_by_identifier(conn, identifier: str) -> Optional[Dict[str, Any]]:
    """Busca un actor por label, code o initials (insensible a mayúsculas)."""
    actors_table = TargetTable.ACTORS.fq_name
    query = text(
        f"""
        SELECT id::text AS id, code, label
        FROM {actors_table}
        WHERE LOWER(label) = LOWER(:identifier)
           OR LOWER(code) = LOWER(:identifier)
           OR LOWER(initials) = LOWER(:identifier)
        LIMIT 1;
        """
    )
    result = await conn.execute(query, {"identifier": identifier.strip()})
    row = result.mappings().first()
    return dict(row) if row else None


async def get_form_by_code(conn, form_code: str) -> Optional[Dict[str, Any]]:
    """Busca un formulario por su código (ej. 'FORM_2019', '2019', etc.)."""
    forms_table = TargetTable.FORMS.fq_name
    query = text(
        f"""
        SELECT id::text AS id, code, label
        FROM {forms_table}
        WHERE LOWER(code) = LOWER(:code)
           OR LOWER(label) LIKE LOWER(:pattern)
        LIMIT 1;
        """
    )
    result = await conn.execute(query, {"code": form_code, "pattern": f"%{form_code}%"})
    row = result.mappings().first()
    return dict(row) if row else None


async def get_submission_status_by_code(
    conn, status_code: str = SubmissionStatusesEnum.SUBMITTED.code
) -> Optional[Dict[str, Any]]:
    """Busca el ID del tipo de estado utilizando el nombre calificado (fq_name)."""
    table_name = TargetTable.SUBMISSION_STATUS_TYPES.fq_name
    query = text(
        f"""
        SELECT id::text AS id, code
        FROM {table_name}
        WHERE LOWER(code) = LOWER(:code)
        LIMIT 1;
        """
    )
    result = await conn.execute(query, {"code": status_code})
    row = result.mappings().first()
    return dict(row) if row else None


async def get_questions_map_for_form(conn, form_id: str) -> Dict[str, str]:
    """Retorna un mapa de {code_pregunta: question_id} pertenecientes a un formulario."""
    questions_table = TargetTable.QUESTIONS.fq_name
    sections_table = TargetTable.SECTIONS.fq_name
    query = text(
        f"""
        SELECT 
            q.id::text AS question_id,
            q.code AS question_code
        FROM {questions_table} q
        JOIN {sections_table} s ON q.section_id = s.id
        WHERE s.form_id = CAST(:form_id AS uuid);
        """
    )
    result = await conn.execute(query, {"form_id": form_id})
    rows = result.mappings().all()
    return {str(row["question_code"]).strip(): row["question_id"] for row in rows}


async def get_existing_submission(
    conn, actor_id: str, form_id: str
) -> Optional[Dict[str, Any]]:
    """Busca si ya existe una entrega para el par (actor_id, form_id)."""
    submissions_table = TargetTable.SUBMISSIONS.fq_name
    query = text(
        f"""
        SELECT id::text AS id, actor_id::text AS actor_id, form_id::text AS form_id
        FROM {submissions_table}
        WHERE actor_id = CAST(:actor_id AS uuid)
          AND form_id = CAST(:form_id AS uuid)
        LIMIT 1;
        """
    )
    result = await conn.execute(query, {"actor_id": actor_id, "form_id": form_id})
    row = result.mappings().first()
    return dict(row) if row else None


# -----------------------------------------------------------------------------
# OPERACIONES DE INSERCIÓN Y ACTUALIZACIÓN
# -----------------------------------------------------------------------------


async def insert_submission(conn, record: dict) -> None:
    """Inserta una nueva entrega en submissions."""
    submissions_table = TargetTable.SUBMISSIONS.fq_name
    query = text(
        f"""
        INSERT INTO {submissions_table} (
            id,
            actor_id,
            form_id,
            status_id,
            created_at,
            updated_at
        )
        VALUES (
            CAST(:id AS uuid),
            CAST(:actor_id AS uuid),
            CAST(:form_id AS uuid),
            CAST(:status_id AS uuid),
            :created_at,
            :updated_at
        );
        """
    )
    await conn.execute(query, record)


async def update_submission(
    conn, submission_id: str, status_id: Optional[str], updated_at: datetime
) -> None:
    """Actualiza una entrega existente."""
    submissions_table = TargetTable.SUBMISSIONS.fq_name
    query = text(
        f"""
        UPDATE {submissions_table}
        SET status_id = CAST(:status_id AS uuid),
            updated_at = :updated_at
        WHERE id = CAST(:id AS uuid);
        """
    )
    await conn.execute(
        query,
        {
            "id": submission_id,
            "status_id": status_id,
            "updated_at": updated_at,
        },
    )


async def upsert_answers(conn, submission_id: str, answers: List[dict]) -> int:
    """Inserta o actualiza respuestas en answers de forma idempotente."""
    if not answers:
        return 0

    answers_table = TargetTable.ANSWERS.fq_name
    now = datetime.now(timezone.utc)
    query = text(
        f"""
        INSERT INTO {answers_table} (
            id,
            submission_id,
            question_id,
            value_numeric,
            value_text,
            created_at,
            updated_at
        )
        VALUES (
            CAST(:id AS uuid),
            CAST(:submission_id AS uuid),
            CAST(:question_id AS uuid),
            :value_numeric,
            :value_text,
            :created_at,
            :updated_at
        )
        ON CONFLICT (submission_id, question_id)
        DO UPDATE SET
            value_numeric = EXCLUDED.value_numeric,
            value_text = EXCLUDED.value_text,
            updated_at = EXCLUDED.updated_at;
        """
    )

    for ans in answers:
        await conn.execute(
            query,
            {
                "id": new_uuidv7(),
                "submission_id": submission_id,
                "question_id": ans["question_id"],
                "value_numeric": ans.get("value_numeric"),
                "value_text": ans.get("value_text"),
                "created_at": now,
                "updated_at": now,
            },
        )

    return len(answers)


# -----------------------------------------------------------------------------
# LECTURA Y PROCESAMIENTO DE ARCHIVOS EXCEL
# -----------------------------------------------------------------------------


def resolve_year_file_path(year: int) -> Optional[Path]:
    """
    Busca los archivos de resultados como hermanos de LOCAL_IIP_STRUCTURE_FILE.
    Prueba variantes: 'resultados <year>.xlsx', 'resultados_<year>.xlsx', '<year>.xlsx'.
    """
    candidates = [
        BASE_DIR / f"resultados {year}.xlsx",
        BASE_DIR / f"resultados_{year}.xlsx",
        BASE_DIR / f"Resultados {year}.xlsx",
        BASE_DIR / f"{year}.xlsx",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def clean_question_code(col_name: Any) -> str:
    """Limpia el nombre de la columna para obtener el código de la pregunta."""
    s = str(col_name).strip().replace("\n", " ")
    match = re.match(r"^(?:Pregunta\s*)?(\d+(?:\.\d+)?)", s, re.IGNORECASE)
    if match:
        return match.group(1)
    return s


def parse_year_excel_file(file_path: Path, year: int) -> List[Dict[str, Any]]:
    """Lee un archivo de resultados de un año y extrae datos de entrega y respuestas."""
    df = pd.read_excel(file_path)
    if df.empty:
        return []

    entity_col = df.columns[0]
    question_cols = df.columns[1:]

    records = []
    for _, row in df.iterrows():
        actor_name = str(row[entity_col]).strip() if pd.notna(row[entity_col]) else None
        if not actor_name or actor_name.lower() in ("nan", "none", "total", "promedio"):
            continue

        raw_answers = []
        for col in question_cols:
            val = row[col]
            if pd.isna(val):
                continue

            q_code = clean_question_code(col)
            val_num = None
            val_text = None

            try:
                val_num = float(val)
            except (ValueError, TypeError):
                val_text = str(val).strip()

            raw_answers.append(
                {
                    "question_code": q_code,
                    "value_numeric": val_num,
                    "value_text": val_text,
                }
            )

        records.append(
            {
                "actor_identifier": actor_name,
                "form_code": f"FORM_{year}",
                "answers": raw_answers,
            }
        )

    return records


# -----------------------------------------------------------------------------
# EJECUCIÓN DEL POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    """Carga las entregas y respuestas del IIP en la base de datos."""
    logger.debug("Starting forms.submissions population...")

    try:
        async with async_engine.begin() as conn:
            # Obtener estado 'SUBMITTED' ('submitted') desde el Enum
            status = await get_submission_status_by_code(
                conn, status_code=SubmissionStatusesEnum.SUBMITTED.code
            )
            status_id = status["id"] if status else None

            if not status_id:
                table_name = TargetTable.SUBMISSION_STATUS_TYPES.fq_name
                logger.warning(
                    f"Status '{SubmissionStatusesEnum.SUBMITTED.code}' not found. Fetching first available status from {table_name}."
                )
                fallback_status_res = await conn.execute(
                    text(f"SELECT id::text FROM {table_name} LIMIT 1;")
                )
                status_row = fallback_status_res.mappings().first()
                if not status_row:
                    raise ValueError(
                        "No submission status types found in database. Seed submission status types first."
                    )
                status_id = status_row["id"]

            total_inserted = 0
            total_updated = 0
            total_answers = 0

            for year in YEARS:
                file_path = resolve_year_file_path(year)
                if not file_path:
                    logger.warning(
                        f"No results file found for year {year} in {BASE_DIR}. Skipping."
                    )
                    continue

                logger.info(
                    f"Processing results file for year {year}: {file_path.name}"
                )
                submissions = parse_year_excel_file(file_path, year)

                # Buscar formulario correspondiente al año
                form = await get_form_by_code(
                    conn, f"FORM_{year}"
                ) or await get_form_by_code(conn, str(year))
                if not form:
                    logger.warning(
                        f"Form for year '{year}' (code FORM_{year}) not found in DB. Skipping year."
                    )
                    continue

                form_id = form["id"]
                questions_map = await get_questions_map_for_form(conn, form_id)

                for entry in submissions:
                    actor_identifier = entry["actor_identifier"]
                    actor = await get_actor_by_identifier(conn, actor_identifier)

                    if not actor:
                        logger.warning(
                            f"Actor '{actor_identifier}' not found in database. Skipping."
                        )
                        continue

                    actor_id = actor["id"]
                    now = datetime.now(timezone.utc)
                    existing = await get_existing_submission(conn, actor_id, form_id)

                    if existing:
                        submission_id = existing["id"]

                        if not is_uuidv7(submission_id):
                            raise ValueError(
                                f"Existing submission for actor '{actor_identifier}' (Form '{form['code']}') "
                                f"has a non-UUIDv7 ID: '{submission_id}'."
                            )

                        await update_submission(conn, submission_id, status_id, now)
                        total_updated += 1
                        logger.debug(
                            f"Updated existing submission '{submission_id}' for Actor '{actor['label']}'"
                        )
                    else:
                        submission_id = new_uuidv7()
                        await insert_submission(
                            conn,
                            {
                                "id": submission_id,
                                "actor_id": actor_id,
                                "form_id": form_id,
                                "status_id": status_id,
                                "created_at": now,
                                "updated_at": now,
                            },
                        )
                        total_inserted += 1
                        logger.debug(
                            f"Inserted new submission '{submission_id}' for Actor '{actor['label']}'"
                        )

                    # Mapear respuestas con question_id reales
                    valid_answers = []
                    for raw_ans in entry["answers"]:
                        q_code = raw_ans["question_code"]
                        question_id = questions_map.get(q_code)
                        if question_id:
                            valid_answers.append(
                                {
                                    "question_id": question_id,
                                    "value_numeric": raw_ans["value_numeric"],
                                    "value_text": raw_ans["value_text"],
                                }
                            )

                    if valid_answers:
                        ans_count = await upsert_answers(
                            conn, submission_id, valid_answers
                        )
                        total_answers += ans_count

        logger.debug(
            f"forms.submissions population finished. "
            f"Submissions Inserted: {total_inserted}, Updated: {total_updated}, Answers Upserted: {total_answers}."
        )

    except Exception as e:
        logger.error(f"Failed to run forms.submissions population: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(upgrade())
