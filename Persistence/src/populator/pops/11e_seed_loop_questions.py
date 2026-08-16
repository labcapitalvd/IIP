"""Puebla las preguntas tipo bucle de 2023 en forms.questions.

Dependencias previas:
    11c_seed_sections.py
    11d_seed_questions.py

Convención de almacenamiento:
- label: código visible del bucle, por ejemplo "Pregunta 1.1".
- description: enunciado completo del bucle.
- helper: NULL (o cadena vacía si la columna no permite NULL).
- file_id: NULL.
- required: TRUE.
- is_loop: TRUE.
- Las ponderaciones Maxb y Max_subpregunta_bucle NO se guardan aquí.

Caso especial:
- Pregunta 28.1 es pregunta principal y bucle al mismo tiempo.
- Se conserva una sola fila en forms.questions.
- El enunciado principal permanece en description.
- El enunciado del bucle se almacenará en forms.card_templates.description.

El script no depende de helper en questions ni en sections y conserva UUIDv7.
"""

from __future__ import annotations

import asyncio
import os
import re
import unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any, TypedDict
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
EXPECTED_SUBQUESTION_COUNT = int(
    os.getenv("IIP_EXPECTED_2023_SUBQUESTION_COUNT", "101")
)


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


def parse_positive_integer(value, context: str) -> int:
    value = clean(value)
    if value is None:
        raise ValueError(f"Valor vacío en {context}.")
    try:
        numeric = float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Valor inválido en {context}: {value!r}") from exc
    if not numeric.is_integer() or numeric <= 0:
        raise ValueError(f"Valor inválido en {context}: {value!r}")
    return int(numeric)


def question_order(value) -> int:
    value = clean(value)
    if value is None:
        return 0
    match = re.search(r"(\d+(?:[.,]\d+)*)", value)
    if not match:
        return 0
    parts = [int(part) for part in match.group(1).replace(",", ".").split(".")]
    if len(parts) == 1:
        return parts[0] * 1000
    order = parts[0] * 1000 + parts[1]
    for part in parts[2:]:
        order = order * 1000 + part
    return order


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


class SubquestionDict(TypedDict):
    order: int
    text: str


class LoopRecord(TypedDict):
    source_row: int
    component: Any
    variable: Any
    indicator: Any
    parent_question: Any
    parent_text: Any
    loop_question: str
    loop_text: Any
    is_mixed: bool
    subquestions: OrderedDict[int, Any] | list[SubquestionDict]


def load_loops(excel: pd.ExcelFile) -> list[LoopRecord]:
    frame = read_sheet(excel, str(YEAR))
    required = {
        "Componente",
        "Variable",
        "Indicador",
        "Pregunta",
        f"Pregunta {YEAR}",
        "Bucle",
        f"Bucle {YEAR}",
        "Orden_subpregunta_bucle",
        "Subpregunta_bucle",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Faltan columnas en la hoja {YEAR}: {sorted(missing)}")

    data = pd.DataFrame(
        {
            "source_row": frame.index + 2,
            "component": frame["Componente"],
            "variable": frame["Variable"],
            "indicator": frame["Indicador"],
            "parent_question": frame["Pregunta"],
            "parent_text": frame[f"Pregunta {YEAR}"],
            "loop_question": frame["Bucle"],
            "loop_text": frame[f"Bucle {YEAR}"],
            "subquestion_order": frame["Orden_subpregunta_bucle"],
            "subquestion_text": frame["Subpregunta_bucle"],
        }
    )

    for column in data.columns:
        if column != "source_row":
            data[column] = data[column].apply(clean)

    fill_columns = [
        "component",
        "variable",
        "indicator",
        "parent_question",
        "parent_text",
    ]
    data[fill_columns] = data[fill_columns].ffill()

    data = data[
        data["component"].notna()
        & data["variable"].notna()
        & data["indicator"].notna()
        & data["parent_question"].notna()
        & data["loop_question"].notna()
        & data["loop_text"].notna()
        & data["subquestion_text"].notna()
    ].copy()

    registry: OrderedDict[str, LoopRecord] = OrderedDict()

    for _, row in data.iterrows():
        loop_question = str(row["loop_question"])
        candidate: LoopRecord = {
            "source_row": int(row["source_row"]),
            "component": row["component"],
            "variable": row["variable"],
            "indicator": row["indicator"],
            "parent_question": row["parent_question"],
            "parent_text": row["parent_text"],
            "loop_question": loop_question,
            "loop_text": row["loop_text"],
            "is_mixed": loop_question == row["parent_question"],
            "subquestions": OrderedDict(),
        }

        current = registry.get(loop_question)
        if current is None:
            registry[loop_question] = candidate
            current = candidate
        else:
            fields = (
                "component",
                "variable",
                "indicator",
                "parent_question",
                "loop_text",
                "is_mixed",
            )
            conflicts = []
            for field in fields:
                left = current[field]  # type: ignore
                right = candidate[field]  # type: ignore
                equal = (
                    left == right
                    if field == "is_mixed"
                    else normalize(left) == normalize(right)
                )
                if not equal:
                    conflicts.append(field)
            if conflicts:
                raise ValueError(
                    f"Información contradictoria para {loop_question}. "
                    f"Campos: {conflicts}. Fila: {candidate['source_row']}."
                )

        order = parse_positive_integer(
            row["subquestion_order"],
            f"Orden_subpregunta_bucle, fila {int(row['source_row'])}",
        )
        text_value = row["subquestion_text"]

        subquestions_dict = current["subquestions"]
        if isinstance(subquestions_dict, OrderedDict):
            previous = subquestions_dict.get(order)
            if previous is not None and normalize(previous) != normalize(text_value):
                raise ValueError(
                    f"Subpregunta contradictoria en {loop_question}, orden {order}."
                )
            subquestions_dict[order] = text_value

    records = list(registry.values())
    records.sort(key=lambda item: question_order(item["loop_question"]))

    total_subquestions = 0
    for record in records:
        subq_map = record["subquestions"]
        if isinstance(subq_map, OrderedDict):
            orders = sorted(subq_map.keys())
            if orders != list(range(1, len(orders) + 1)):
                raise ValueError(
                    f"Órdenes no consecutivos en {record['loop_question']}: {orders}"
                )
            record["subquestions"] = [
                {
                    "order": int(order),
                    "text": subq_map[order],
                }
                for order in orders
            ]
            total_subquestions += len(orders)

    if len(records) != EXPECTED_LOOP_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_LOOP_COUNT} bucles y se encontraron "
            f"{len(records)}."
        )
    if total_subquestions != EXPECTED_SUBQUESTION_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_SUBQUESTION_COUNT} subpreguntas de bucle "
            f"y se encontraron {total_subquestions}."
        )

    mixed = [record for record in records if record["is_mixed"]]
    if len(mixed) != 1:
        raise ValueError(
            f"Se esperaba un único bucle mixto y se encontraron {len(mixed)}."
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
        {"year": str(YEAR)},  # <--- Casteado a string
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


async def get_indicator_map(conn) -> dict[tuple[str, str, str], str]:
    result = await conn.execute(
        text(
            """
            SELECT
                component.label AS component_label,
                variable.label AS variable_label,
                indicator.label AS indicator_label,
                indicator.id::text AS indicator_id
            FROM forms.sections indicator
            JOIN forms.section_types indicator_type
              ON indicator_type.id = indicator.section_type_id
             AND UPPER(TRIM(indicator_type.label)) = 'INDICADOR'
            JOIN forms.sections variable
              ON variable.id = indicator.parent_id
            JOIN forms.section_types variable_type
              ON variable_type.id = variable.section_type_id
             AND UPPER(TRIM(variable_type.label)) = 'VARIABLE'
            JOIN forms.sections component
              ON component.id = variable.parent_id
            JOIN forms.section_types component_type
              ON component_type.id = component.section_type_id
             AND UPPER(TRIM(component_type.label)) = 'COMPONENTE'
            JOIN forms.forms form
              ON form.id = indicator.form_id
            WHERE form.code = :year;
            """
        ),
        {"year": str(YEAR)},  # <--- Casteado a string
    )

    lookup: dict[tuple[str, str, str], str] = {}
    for row in result.mappings().all():
        indicator_id = row["indicator_id"]
        if not is_uuidv7(indicator_id):
            raise ValueError(f"Indicador no UUIDv7: {indicator_id}")
        key = (
            normalize(row["component_label"]),
            normalize(row["variable_label"]),
            normalize(row["indicator_label"]),
        )
        if key in lookup and lookup[key] != indicator_id:
            raise ValueError(f"Indicador ambiguo para {key}.")
        lookup[key] = indicator_id

    return lookup


async def get_question_map(conn, form_id: str) -> dict[str, dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                q.id::text AS question_id,
                q.section_id::text AS section_id,
                q.code,
                q.label,
                q.description,
                q.display_order,
                q.required,
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
                f"Preguntas duplicadas para label {key}: "
                f"{[row['question_id'] for row in rows]}"
            )
        if not is_uuidv7(rows[0]["question_id"]):
            raise ValueError(f"Pregunta existente sin UUIDv7: {rows[0]['question_id']}")
        lookup[key] = rows[0]

    return lookup


async def save_independent_loop(conn, record: dict, update: bool) -> None:
    if update:
        statement = text(
            """
            UPDATE forms.questions
            SET
                code = :code,
                section_id = CAST(:section_id AS uuid),
                file_id = NULL,
                label = :label,
                description = :description,
                helper = :helper,
                display_order = :display_order,
                required = TRUE,
                is_loop = TRUE,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
            """
        )
    else:
        statement = text(
            """
            INSERT INTO forms.questions (
                id,
                code,
                section_id,
                file_id,
                label,
                description,
                helper,
                display_order,
                required,
                is_loop,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                :code,
                CAST(:section_id AS uuid),
                NULL,
                :label,
                :description,
                :helper,
                :display_order,
                TRUE,
                TRUE,
                NOW()
            );
            """
        )
    await conn.execute(statement, record)


async def update_mixed_loop(
    conn,
    question_id: str,
    section_id: str,
    helper_value,
) -> None:
    await conn.execute(
        text(
            """
            UPDATE forms.questions
            SET
                section_id = CAST(:section_id AS uuid),
                helper = :helper,
                required = TRUE,
                is_loop = TRUE,
                updated_at = NOW()
            WHERE id = CAST(:question_id AS uuid);
            """
        ),
        {
            "question_id": question_id,
            "section_id": section_id,
            "helper": helper_value,
        },
    )


async def validate_loaded(
    conn,
    loops: list[LoopRecord],
    form_id: str,
    indicators: dict[tuple[str, str, str], str],
) -> None:
    questions = await get_question_map(conn, form_id)

    for loop in loops:
        key = normalize(loop["loop_question"])
        question = questions.get(key)
        if question is None:
            raise ValueError(f"No se cargó el bucle {loop['loop_question']}.")

        expected_section = indicators[
            (
                normalize(loop["component"]),
                normalize(loop["variable"]),
                normalize(loop["indicator"]),
            )
        ]

        if question["section_id"] != expected_section:
            raise ValueError(f"section_id incorrecto para {loop['loop_question']}.")
        if question["is_loop"] is not True:
            raise ValueError(f"is_loop debe ser TRUE para {loop['loop_question']}.")
        if question["required"] is not True:
            raise ValueError(f"required debe ser TRUE para {loop['loop_question']}.")
        if not is_uuidv7(question["question_id"]):
            raise ValueError(f"UUID no es versión 7 para {loop['loop_question']}.")

        if not loop["is_mixed"]:
            if normalize(question["description"]) != normalize(loop["loop_text"]):
                raise ValueError(
                    f"description incorrecta para {loop['loop_question']}."
                )

    logger.info(f"Loop questions validation passed. Validated: {len(loops)}.")


# -----------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:

    path = Path(FILE_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    logger.info(f"Starting loop questions population from {path}")

    excel = pd.ExcelFile(path)
    loops = load_loops(excel)

    async with async_engine.begin() as conn:
        columns = await table_columns(conn, "forms", "questions")
        required_columns = {
            "id",
            "code",
            "section_id",
            "file_id",
            "label",
            "description",
            "helper",
            "display_order",
            "required",
            "is_loop",
            "updated_at",
        }
        missing = required_columns - set(columns)
        if missing:
            raise ValueError(f"Faltan columnas en forms.questions: {sorted(missing)}")

        form_id = await get_form(conn)
        indicators = await get_indicator_map(conn)
        questions = await get_question_map(conn, form_id)
        helper_value = None if columns["helper"]["nullable"] else ""

        inserted = 0
        updated = 0
        mixed_updated = 0

        for loop in loops:
            hierarchy_key = (
                normalize(loop["component"]),
                normalize(loop["variable"]),
                normalize(loop["indicator"]),
            )
            section_id = indicators.get(hierarchy_key)
            if section_id is None:
                raise ValueError(
                    f"No se encontró INDICADOR para {loop['loop_question']}. "
                    f"Jerarquía: {hierarchy_key}"
                )

            parent = questions.get(normalize(loop["parent_question"]))
            if parent is None:
                raise ValueError(
                    f"No existe la pregunta principal "
                    f"{loop['parent_question']} para {loop['loop_question']}. "
                    "Ejecuta antes 11d_seed_questions.py."
                )
            if parent["section_id"] != section_id:
                raise ValueError(
                    f"{loop['parent_question']} y {loop['loop_question']} "
                    "no pertenecen al mismo indicador."
                )

            existing = questions.get(normalize(loop["loop_question"]))

            if loop["is_mixed"]:
                if existing is None or existing["question_id"] != parent["question_id"]:
                    raise ValueError(
                        f"El bucle mixto {loop['loop_question']} debe reutilizar "
                        "la pregunta principal existente."
                    )
                await update_mixed_loop(
                    conn,
                    question_id=parent["question_id"],
                    section_id=section_id,
                    helper_value=helper_value,
                )
                mixed_updated += 1
                continue

            question_id = existing["question_id"] if existing else new_uuidv7()
            if not is_uuidv7(question_id):
                raise ValueError(f"ID no UUIDv7: {question_id}")

            raw_num = re.sub(r"[^\d.]", "", loop["loop_question"]).replace(".", "_")
            code = (
                f"Q{raw_num}" if raw_num else f"{loop['loop_question']}"
            )

            db_record = {
                "id": question_id,
                "code": code,
                "section_id": section_id,
                "label": truncate(
                    loop["loop_question"], columns["label"]["max_length"]
                ),
                "description": truncate(
                    loop["loop_text"],
                    columns["description"]["max_length"],
                ),
                "helper": helper_value,
                "display_order": question_order(loop["loop_question"]),
            }

            await save_independent_loop(
                conn,
                db_record,
                update=existing is not None,
            )
            if existing:
                updated += 1
            else:
                inserted += 1

            questions[normalize(loop["loop_question"])] = {
                "question_id": question_id,
                "section_id": section_id,
                "code": code,
                "label": loop["loop_question"],
                "description": loop["loop_text"],
                "display_order": db_record["display_order"],
                "required": True,
                "is_loop": True,
            }

        await validate_loaded(conn, loops, form_id, indicators)

    logger.info(
        "Loop questions population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}. "
        f"Mixed updated: {mixed_updated}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
