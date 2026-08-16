"""Puebla forms.card_templates para los bucles del IIP 2023.

Dependencias previas:
    11d_seed_questions.py
    11e_seed_loop_questions.py

Convención de almacenamiento:
- question_id: pregunta tipo bucle correspondiente.
- label: código visible del bucle, por ejemplo "Pregunta 1.1".
- description: enunciado completo del bucle.
- helper: NULL (o cadena vacía si la columna no permite NULL).
- No se almacenan ponderaciones ni metadatos técnicos en description/helper.

Se crea exactamente una plantilla por cada pregunta tipo bucle. La pregunta
mixta Pregunta 28.1 utiliza su mismo question_id.
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
YEAR = 2023
EXPECTED_LOOP_COUNT = int(os.getenv("IIP_EXPECTED_2023_LOOP_COUNT", "27"))


# -----------------------------------------------------------------------------
# UTILIDADES
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# EXCEL
# -----------------------------------------------------------------------------


def load_loops(excel: pd.ExcelFile) -> list[dict]:
    frame = read_sheet(excel, str(YEAR))
    required = {"Pregunta", "Bucle", f"Bucle {YEAR}"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Faltan columnas en la hoja {YEAR}: {sorted(missing)}")

    registry: OrderedDict[str, dict] = OrderedDict()

    for row_idx, (index, row) in enumerate(frame.iterrows(), start=2):
        loop_question = clean(row["Bucle"])
        loop_text = clean(row[f"Bucle {YEAR}"])
        parent_question = clean(row["Pregunta"])

        if loop_question is None:
            continue
        if loop_text is None or parent_question is None:
            raise ValueError(f"Bucle incompleto en fila {row_idx}.")

        candidate = {
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
            raise ValueError(f"Información contradictoria para {loop_question}.")

    records = list(registry.values())
    if len(records) != EXPECTED_LOOP_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_LOOP_COUNT} bucles y se encontraron "
            f"{len(records)}."
        )
    return records


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


async def get_form(conn) -> str:
    result = await conn.execute(
        text("SELECT id::text AS id FROM forms.forms WHERE code = :year;"),
        {"year": YEAR},
    )
    rows = result.mappings().all()
    if len(rows) != 1:
        raise ValueError(
            f"Debe existir un único formulario {YEAR}; encontrados: {len(rows)}."
        )
    form_id = rows[0]["id"]
    if not is_uuidv7(form_id):
        raise ValueError(f"form_id de {YEAR} no es UUIDv7: {form_id}")
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
            -- FIX: Join on sections table to safely access the missing form_id link
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
                label,
                description,
                helper,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:question_id AS uuid),
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

    logger.info(f"forms.card_templates validation passed. Validated: {len(expected)}.")


# -----------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:

    path = Path(FILE_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    logger.info(f"Starting forms.card_templates population from {path}")

    excel = pd.ExcelFile(path)
    loops = load_loops(excel)

    async with async_engine.begin() as conn:
        columns = await table_columns(conn, "forms", "card_templates")
        required = {
            "id",
            "question_id",
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

        form_id = await get_form(conn)
        questions = await get_questions(conn, form_id)
        existing = await get_existing_templates(conn)
        helper_value = None if columns["helper"]["nullable"] else ""

        inserted = 0
        updated = 0

        for source in loops:
            question = questions.get(normalize(source["loop_question"]))
            if question is None:
                raise ValueError(
                    f"No existe {source['loop_question']} en forms.questions. "
                    "Ejecuta antes 11e_seed_loop_questions.py."
                )
            if question["is_loop"] is not True:
                raise ValueError(
                    f"{source['loop_question']} tiene is_loop distinto de TRUE."
                )

            old = existing.get(question["question_id"])
            card_template_id = old["card_template_id"] if old else new_uuidv7()
            if not is_uuidv7(card_template_id):
                raise ValueError(f"ID no UUIDv7: {card_template_id}")

            db_record = {
                "id": card_template_id,
                "question_id": question["question_id"],
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

        await validate_loaded(conn, loops, questions)

    logger.info(
        "forms.card_templates population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
