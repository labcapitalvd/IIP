"""Puebla las preguntas principales del IIP en forms.questions.

Fuente:
    Estructura_IIP.xlsx

Años activos:
    2019, 2021 y 2023

Convención de almacenamiento:
- label: código visible de la pregunta, por ejemplo "Pregunta 1".
- description: enunciado completo de la pregunta.
- helper: NULL (o cadena vacía si la columna no permite NULL).
- file_id: NULL.
- required: TRUE.
- is_loop: TRUE únicamente cuando una pregunta principal también es un bucle.
  En el archivo actual esto ocurre con Pregunta 28.1 de 2023.
- Los valores Maxp, Maxb y demás ponderaciones NO se guardan aquí.

Relaciones:
- form_id -> forms.forms.id
- section_id -> forms.sections.id del INDICADOR correspondiente

El script es idempotente y conserva UUIDv7 existentes.
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
from sqlalchemy import text
from uuid_utils import uuid7

from shared_db import async_engine
from shared_utils.logger import get_logger


logger = get_logger("pop/questions")

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)
DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023)


# -----------------------------------------------------------------------------
# UTILIDADES
# -----------------------------------------------------------------------------


def active_years() -> tuple[int, ...]:
    raw = os.getenv("IIP_ACTIVE_YEARS")
    if not raw:
        return DEFAULT_ACTIVE_YEARS

    years: list[int] = []
    for value in raw.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            years.append(int(value))
        except ValueError as exc:
            raise ValueError(f"Año inválido en IIP_ACTIVE_YEARS: {value!r}") from exc

    if not years or len(years) != len(set(years)):
        raise ValueError(
            f"IIP_ACTIVE_YEARS debe contener años únicos y válidos: {years}"
        )

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


def display_order_from_question(value) -> int:
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


# -----------------------------------------------------------------------------
# LECTURA DEL EXCEL
# -----------------------------------------------------------------------------


def load_questions(excel: pd.ExcelFile, years: tuple[int, ...]) -> list[dict]:
    """Construye preguntas principales únicas y su jerarquía metodológica."""
    records: list[dict] = []

    for year in years:
        frame = read_sheet(excel, str(year))
        required = {
            "Componente",
            "Variable",
            "Indicador",
            "Pregunta",
            f"Pregunta {year}",
        }
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"Faltan columnas en la hoja {year}: {sorted(missing)}")

        has_loop_columns = "Bucle" in frame.columns and f"Bucle {year}" in frame.columns

        data = pd.DataFrame(
            {
                "source_row": frame.index + 2,
                "component": frame["Componente"],
                "variable": frame["Variable"],
                "indicator": frame["Indicador"],
                "question": frame["Pregunta"],
                "question_text": frame[f"Pregunta {year}"],
                "loop": frame["Bucle"] if has_loop_columns else None,
            }
        )

        for column in data.columns:
            if column != "source_row":
                data[column] = data[column].apply(clean)

        hierarchy = ["component", "variable", "indicator"]
        data[hierarchy] = data[hierarchy].ffill()

        data = data[
            data["component"].notna()
            & data["variable"].notna()
            & data["indicator"].notna()
            & data["question"].notna()
            & data["question_text"].notna()
        ].copy()

        registry: OrderedDict[str, dict] = OrderedDict()

        for _, row in data.iterrows():
            question = row["question"]
            candidate = {
                "year": year,
                "source_row": int(row["source_row"]),
                "component": row["component"],
                "variable": row["variable"],
                "indicator": row["indicator"],
                "question": question,
                "question_text": row["question_text"],
                "is_loop": clean(row["loop"]) == question,
                "display_order": display_order_from_question(question),
            }

            existing = registry.get(question)
            if existing is None:
                registry[question] = candidate
                continue

            fields = (
                "component",
                "variable",
                "indicator",
                "question_text",
            )
            conflicts = [
                field
                for field in fields
                if normalize(existing[field]) != normalize(candidate[field])
            ]
            if conflicts:
                raise ValueError(
                    f"Información contradictoria para {question} en {year}. "
                    f"Campos: {conflicts}. Filas: "
                    f"{existing['source_row']} y {candidate['source_row']}."
                )

            existing["is_loop"] = existing["is_loop"] or candidate["is_loop"]

        year_records = list(registry.values())
        if not year_records:
            raise ValueError(f"La hoja {year} no produjo preguntas válidas.")

        records.extend(year_records)
        logger.info(f"Year {year}: {len(year_records)} preguntas principales.")

    return records


# -----------------------------------------------------------------------------
# POSTGRESQL
# -----------------------------------------------------------------------------


async def table_columns(conn, schema: str, table: str) -> dict:
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                character_maximum_length,
                is_nullable
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


async def get_forms(conn, years: tuple[int, ...]) -> dict[int, str]:
    result = await conn.execute(
        text("SELECT anno, id::text AS id FROM forms.forms ORDER BY anno;")
    )

    grouped: dict[int, list[str]] = defaultdict(list)
    for row in result.mappings().all():
        year = int(row["anno"])
        if year in years:
            grouped[year].append(row["id"])

    lookup: dict[int, str] = {}
    for year in years:
        ids = grouped.get(year, [])
        if len(ids) != 1:
            raise ValueError(
                f"Debe existir un único formulario para {year}; "
                f"encontrados: {len(ids)}."
            )
        if not is_uuidv7(ids[0]):
            raise ValueError(f"form_id de {year} no es UUIDv7: {ids[0]}")
        lookup[year] = ids[0]

    return lookup


async def get_indicator_map(
    conn,
    years: tuple[int, ...],
) -> dict[tuple[int, str, str, str], str]:
    """Relaciona año + códigos visibles de la jerarquía con INDICADOR."""
    result = await conn.execute(
        text(
            """
            SELECT
                form.anno,
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
            ORDER BY form.anno, component.label, variable.label, indicator.label;
            """
        )
    )

    lookup: dict[tuple[int, str, str, str], str] = {}
    for row in result.mappings().all():
        year = int(row["anno"])
        if year not in years:
            continue

        indicator_id = row["indicator_id"]
        if not is_uuidv7(indicator_id):
            raise ValueError(f"Indicador no UUIDv7: {indicator_id}")

        key = (
            year,
            normalize(row["component_label"]),
            normalize(row["variable_label"]),
            normalize(row["indicator_label"]),
        )

        if key in lookup and lookup[key] != indicator_id:
            raise ValueError(f"Indicador ambiguo para la llave {key}.")

        lookup[key] = indicator_id

    return lookup


async def get_existing_questions(
    conn,
    years: tuple[int, ...],
) -> dict[tuple[int, str], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                question.section_id::text AS section_id,
                question.label,
                question.description,
                question.display_order,
                question.required,
                question.is_loop,
                form.anno
            FROM forms.questions question
            JOIN forms.sections section 
              ON section.id = question.section_id
            JOIN forms.forms form 
              ON form.id = section.form_id
            ORDER BY form.anno, question.label, question.id;
            """
        )
    )

    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        year = int(row["anno"])
        if year in years:
            grouped[(year, normalize(row["label"]))].append(dict(row))

    existing: dict[tuple[int, str], dict] = {}
    for key, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                f"Existen preguntas duplicadas para {key}: "
                f"{[row['question_id'] for row in rows]}"
            )
        if not is_uuidv7(rows[0]["question_id"]):
            raise ValueError(f"Pregunta existente sin UUIDv7: {rows[0]['question_id']}")
        existing[key] = rows[0]

    return existing


async def save_question(conn, record: dict, update: bool) -> None:
    if update:
        statement = text(
            """
            UPDATE forms.questions
            SET
                section_id = CAST(:section_id AS uuid),
                file_id = NULL,
                label = :label,
                description = :description,
                helper = :helper,
                display_order = :display_order,
                required = :required,
                is_loop = :is_loop,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
            """
        )
    else:
        statement = text(
            """
            INSERT INTO forms.questions (
                id,
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
                CAST(:section_id AS uuid),
                NULL,
                :label,
                :description,
                :helper,
                :display_order,
                :required,
                :is_loop,
                NOW()
            );
            """
        )

    await conn.execute(statement, record)


async def validate_loaded(
    conn,
    source_records: list[dict],
    forms: dict[int, str],
    indicators: dict[tuple[int, str, str, str], str],
) -> None:
    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                question.section_id::text AS section_id,
                question.label,
                question.description,
                question.helper,
                question.required,
                question.is_loop,
                form.anno,
                section_type.label AS section_type
            FROM forms.questions question
            JOIN forms.sections section
              ON section.id = question.section_id
            JOIN forms.forms form
              ON form.id = section.form_id
            LEFT JOIN forms.section_types section_type
              ON section_type.id = section.section_type_id
            ORDER BY form.anno, question.label;
            """
        )
    )

    by_key: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        by_key[(int(row["anno"]), normalize(row["label"]))].append(dict(row))

    for source in source_records:
        key = (source["year"], normalize(source["question"]))
        rows = by_key.get(key, [])
        if len(rows) != 1:
            raise ValueError(
                f"Validación fallida para {source['year']} / "
                f"{source['question']}: coincidencias={len(rows)}."
            )

        row = rows[0]
        hierarchy_key = (
            source["year"],
            normalize(source["component"]),
            normalize(source["variable"]),
            normalize(source["indicator"]),
        )
        expected_section_id = indicators[hierarchy_key]

        # Validación corregida: ya no se busca row["form_id"]
        if row["section_id"] != expected_section_id:
            raise ValueError(f"section_id incorrecto para {key}.")
        if normalize(row["description"]) != normalize(source["question_text"]):
            raise ValueError(f"description incorrecta para {key}.")
        if clean(row["helper"]) is not None:
            raise ValueError(f"helper debe quedar vacío para {key}.")
        if row["required"] is not True:
            raise ValueError(f"required debe ser TRUE para {key}.")
        if row["is_loop"] is not bool(source["is_loop"]):
            raise ValueError(f"is_loop incorrecto para {key}.")
        if (clean(row["section_type"]) or "").upper() != "INDICADOR":
            raise ValueError(f"{key} no está conectado a un INDICADOR.")
        if not is_uuidv7(row["question_id"]):
            raise ValueError(f"UUID no es versión 7 para {key}.")

    logger.info(
        f"forms.questions validation passed. "
        f"Validated: {len(source_records)} preguntas principales."
    )


# -----------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade(gh=None, api=None) -> None:
    del gh, api

    path = Path(FILE_PATH)
    years = active_years()

    logger.info(f"Starting forms.questions population from {path}")

    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    excel = pd.ExcelFile(path)
    source_records = load_questions(excel, years)

    async with async_engine.begin() as conn:
        columns = await table_columns(conn, "forms", "questions")
        required_columns = {
            "id",
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

        forms = await get_forms(conn, years)
        indicators = await get_indicator_map(conn, years)
        existing = await get_existing_questions(conn, years)

        inserted = 0
        updated = 0

        for source in source_records:
            hierarchy_key = (
                source["year"],
                normalize(source["component"]),
                normalize(source["variable"]),
                normalize(source["indicator"]),
            )
            section_id = indicators.get(hierarchy_key)
            if section_id is None:
                raise ValueError(
                    "No se encontró el INDICADOR para "
                    f"{source['year']} / {source['question']}. "
                    f"Jerarquía: {hierarchy_key}"
                )

            natural_key = (
                source["year"],
                normalize(source["question"]),
            )
            old = existing.get(natural_key)

            question_id = old["question_id"] if old else new_uuidv7()
            if not is_uuidv7(question_id):
                raise ValueError(f"ID no UUIDv7: {question_id}")

            helper_value = None if columns["helper"]["nullable"] else ""
            db_record = {
                "id": question_id,
                "form_id": forms[source["year"]],
                "section_id": section_id,
                "label": truncate(source["question"], columns["label"]["max_length"]),
                "description": truncate(
                    source["question_text"],
                    columns["description"]["max_length"],
                ),
                "helper": helper_value,
                "display_order": int(source["display_order"]),
                "required": True,
                "is_loop": bool(source["is_loop"]),
            }

            await save_question(conn, db_record, update=old is not None)
            if old:
                updated += 1
            else:
                inserted += 1

        await validate_loaded(conn, source_records, forms, indicators)

    logger.info(
        "forms.questions population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
