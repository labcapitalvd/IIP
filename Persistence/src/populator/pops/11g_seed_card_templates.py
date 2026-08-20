"""Puebla forms.card_templates para los bucles de los formularios IIP.

Dependencias previas:
    11d_seed_questions.py
    11e_seed_loop_questions.py

Convención de almacenamiento:
- question_id: pregunta tipo bucle correspondiente.
- code: código técnico del card_template (ej. "CT_2023_Q28_1").
- label: código visible del bucle, por ejemplo "Pregunta 1.1".
- description: enunciado completo del bucle.
- helper: NULL (o cadena vacía si la columna no permite NULL).
"""

from __future__ import annotations

import asyncio
import os
import re
import unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path
from uuid import UUID

import pandas as pd
from shared.infrastructure import async_engine
from shared.utils.logger import get_logger
from sqlalchemy import text
from uuid_utils import uuid7

logger = get_logger(__name__)

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

DEFAULT_ACTIVE_YEARS = (2023, 2025)


# -----------------------------------------------------------------------------
# UTILIDADES
# -----------------------------------------------------------------------------


def get_active_years() -> tuple[int, ...]:
    raw_value = os.getenv("IIP_ACTIVE_YEARS")
    if not raw_value:
        return DEFAULT_ACTIVE_YEARS

    years: list[int] = []
    for value in raw_value.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            years.append(int(value))
        except ValueError as exc:
            raise ValueError(f"IIP_ACTIVE_YEARS inválido: {value!r}") from exc

    if not years:
        raise ValueError("IIP_ACTIVE_YEARS no contiene años válidos.")

    return tuple(years)


def clean(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    value = str(value).strip()
    return value or None


def normalize(value):
    value = clean(value)
    if value is None:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character for character in value if not unicodedata.combining(character)
    )
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def is_uuidv7(value) -> bool:
    try:
        return UUID(str(value)).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    return str(uuid7())


def truncate(value, max_length):
    value = clean(value)
    if value is None or max_length is None:
        return value
    return value[:max_length]


def read_sheet(excel: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    if sheet_name not in excel.sheet_names:
        raise ValueError(
            f"No existe la hoja {sheet_name!r}. Hojas disponibles: {excel.sheet_names}"
        )
    frame = pd.read_excel(excel, sheet_name=sheet_name, dtype=object)
    frame.columns = [str(column).strip() for column in frame.columns]
    return frame


def make_template_code(year: int, loop_question_label: str) -> str:
    """Genera un código técnico limpio y consistente para la plantilla.

    Ejemplos:
        Pregunta 1.1 -> CT_2023_Q1_1
        Pregunta 28.1 -> CT_2023_Q28_1
    """
    raw_num = re.sub(r"[^\d.]", "", loop_question_label).replace(".", "_")
    if raw_num:
        return f"{year}_CT_Q{raw_num}"

    clean_label = re.sub(r"[^A-Za-z0-9]+", "_", loop_question_label).strip("_")
    return f"{year}_CT_{clean_label}"


# -----------------------------------------------------------------------------
# EXCEL
# -----------------------------------------------------------------------------


def load_loops(excel: pd.ExcelFile, year: int) -> list[dict]:
    sheet_name = str(year)
    if sheet_name not in excel.sheet_names:
        logger.warning(f"Hoja para el año {year} no encontrada en el Excel. Omitiendo.")
        return []

    frame = read_sheet(excel, sheet_name)

    # Evaluar columnas requeridas (soportando variantes con/sin año en la columna Bucle)
    bucle_col = f"Bucle {year}" if f"Bucle {year}" in frame.columns else "Bucle"
    required = {"Pregunta", "Bucle"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Faltan columnas en la hoja {year}: {sorted(missing)}")

    registry: OrderedDict[str, dict] = OrderedDict()

    for row_idx, (_, row) in enumerate(frame.iterrows(), start=2):
        loop_question = clean(row["Bucle"])
        loop_text = clean(row.get(bucle_col)) or loop_question
        parent_question = clean(row["Pregunta"])

        if loop_question is None:
            continue
        if loop_text is None or parent_question is None:
            raise ValueError(f"Bucle incompleto en fila {row_idx} de la hoja {year}.")

        candidate = {
            "year": year,
            "loop_question": loop_question,
            "loop_text": loop_text,
            "parent_question": parent_question,
            "is_mixed": loop_question == parent_question,
        }

        existing = registry.get(loop_question)
        if existing is None:
            registry[loop_question] = candidate
            continue

        if normalize(existing["loop_text"]) != normalize(loop_text) or normalize(
            existing["parent_question"]
        ) != normalize(parent_question):
            raise ValueError(
                f"Información contradictoria para {loop_question} en año {year}."
            )

    return list(registry.values())


# -----------------------------------------------------------------------------
# POSTGRESQL
# -----------------------------------------------------------------------------


async def table_columns(conn, schema: str, table: str) -> dict:
    result = await conn.execute(
        text(
            """
            SELECT column_name, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
            ORDER BY ordinal_position;
            """
        ),
        {"schema": schema, "table": table},
    )
    rows = result.mappings().all()
    if not rows:
        raise ValueError(f"No existe {schema}.{table}.")
    return {
        row["column_name"]: {
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


async def get_form(conn, year: int) -> str | None:
    result = await conn.execute(
        text("SELECT id::text AS id FROM forms.forms WHERE code = :year;"),
        {"year": str(year)},
    )
    rows = result.mappings().all()
    if len(rows) == 0:
        return None
    if len(rows) > 1:
        raise ValueError(
            f"Existe más de un formulario con código {year}; encontrados: {len(rows)}."
        )
    form_id = rows[0]["id"]
    if not is_uuidv7(form_id):
        raise ValueError(f"form_id de {year} no es UUIDv7: {form_id}")
    return form_id


async def get_questions(conn, form_id: str) -> dict[str, dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                q.id::text AS question_id,
                q.label,
                q.description,
                q.is_loop
            FROM forms.questions q
            JOIN forms.sections s ON q.section_id = s.id
            WHERE s.form_id = CAST(:form_id AS uuid)
            ORDER BY q.label, q.id;
            """
        ),
        {"form_id": form_id},
    )

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[normalize(row["label"])].append(dict(row))

    lookup: dict[str, dict] = {}
    for key, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                f"Preguntas duplicadas para {key}: "
                f"{[row['question_id'] for row in rows]}"
            )
        if not is_uuidv7(rows[0]["question_id"]):
            raise ValueError(f"Pregunta sin UUIDv7: {rows[0]['question_id']}")
        lookup[key] = rows[0]

    return lookup


async def get_existing_templates(conn) -> dict[str, dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                id::text AS card_template_id,
                question_id::text AS question_id,
                code,
                label,
                description,
                helper
            FROM forms.card_templates
            ORDER BY question_id, id;
            """
        )
    )

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[row["question_id"]].append(dict(row))

    lookup: dict[str, dict] = {}
    for question_id, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                f"La pregunta {question_id} tiene varios card_templates: "
                f"{[row['card_template_id'] for row in rows]}"
            )
        if not is_uuidv7(rows[0]["card_template_id"]):
            raise ValueError(f"card_template sin UUIDv7: {rows[0]['card_template_id']}")
        lookup[question_id] = rows[0]

    return lookup


async def save_template(conn, record: dict, update: bool) -> None:
    if update:
        statement = text(
            """
            UPDATE forms.card_templates
            SET
                question_id = CAST(:question_id AS uuid),
                code = :code,
                label = :label,
                description = :description,
                helper = :helper,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
            """
        )
    else:
        statement = text(
            """
            INSERT INTO forms.card_templates (
                id,
                question_id,
                code,
                label,
                description,
                helper,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:question_id AS uuid),
                :code,
                :label,
                :description,
                :helper,
                NOW()
            );
            """
        )
    await conn.execute(statement, record)


async def validate_loaded(
    conn,
    expected: list[dict],
    question_map: dict[str, dict],
    year: int,
) -> None:
    existing = await get_existing_templates(conn)

    for source in expected:
        question = question_map.get(normalize(source["loop_question"]))
        if question is None:
            raise ValueError(
                f"No existe la pregunta de bucle {source['loop_question']}."
            )

        template = existing.get(question["question_id"])
        if template is None:
            raise ValueError(
                f"No se cargó card_template para {source['loop_question']}."
            )

        expected_code = make_template_code(year, source["loop_question"])
        if template["code"] != expected_code:
            raise ValueError(
                f"code incorrecto para card_template de {source['loop_question']}: "
                f"{template['code']!r} != {expected_code!r}"
            )
        if normalize(template["label"]) != normalize(source["loop_question"]):
            raise ValueError(
                f"label incorrecto para card_template de {source['loop_question']}."
            )
        if normalize(template["description"]) != normalize(source["loop_text"]):
            raise ValueError(
                f"description incorrecta para card_template de "
                f"{source['loop_question']}."
            )
        if clean(template["helper"]) is not None:
            raise ValueError(
                f"helper debe quedar vacío para {source['loop_question']}."
            )
        if not is_uuidv7(template["card_template_id"]):
            raise ValueError(f"UUID no es versión 7 para {source['loop_question']}.")

    logger.debug(
        f"forms.card_templates validation passed for year {year}. Validated: {len(expected)}."
    )


# -----------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(FILE_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    active_years = get_active_years()
    logger.debug(
        f"Starting forms.card_templates population from {path} for years: {active_years}"
    )

    excel = pd.ExcelFile(path)

    async with async_engine.begin() as conn:
        columns = await table_columns(conn, "forms", "card_templates")
        required = {
            "id",
            "question_id",
            "code",
            "label",
            "description",
            "helper",
            "updated_at",
        }
        missing = required - set(columns)
        if missing:
            raise ValueError(
                f"Faltan columnas en forms.card_templates: {sorted(missing)}"
            )

        helper_value = None if columns["helper"]["nullable"] else ""
        existing = await get_existing_templates(conn)

        total_inserted = 0
        total_updated = 0

        for year in active_years:
            loops = load_loops(excel, year)
            if not loops:
                continue

            form_id = await get_form(conn, year)
            if not form_id:
                logger.warning(
                    f"No existe el formulario con código {year} en BD. Omitiendo año."
                )
                continue

            questions = await get_questions(conn, form_id)

            inserted = 0
            updated = 0

            for source in loops:
                question = questions.get(normalize(source["loop_question"]))
                if question is None:
                    raise ValueError(
                        f"No existe {source['loop_question']} en forms.questions para el año {year}. "
                        "Ejecuta antes 11e_seed_loop_questions.py."
                    )
                if question["is_loop"] is not True:
                    raise ValueError(
                        f"{source['loop_question']} (Año {year}) tiene is_loop distinto de TRUE."
                    )

                old = existing.get(question["question_id"])
                card_template_id = old["card_template_id"] if old else new_uuidv7()
                if not is_uuidv7(card_template_id):
                    raise ValueError(f"ID no UUIDv7: {card_template_id}")

                template_code = make_template_code(year, source["loop_question"])

                db_record = {
                    "id": card_template_id,
                    "question_id": question["question_id"],
                    "code": truncate(template_code, columns["code"]["max_length"]),
                    "label": truncate(
                        source["loop_question"], columns["label"]["max_length"]
                    ),
                    "description": truncate(
                        source["loop_text"],
                        columns["description"]["max_length"],
                    ),
                    "helper": helper_value,
                }

                await save_template(conn, db_record, update=old is not None)
                if old:
                    updated += 1
                else:
                    inserted += 1

            await validate_loaded(conn, loops, questions, year)
            total_inserted += inserted
            total_updated += updated

    logger.debug(
        "forms.card_templates population finished successfully. "
        f"Total Inserted: {total_inserted}. Total Updated: {total_updated}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
