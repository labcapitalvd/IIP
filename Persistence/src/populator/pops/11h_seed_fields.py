"""Puebla forms.fields para los IIP.

Dependencias previas:
    11d_seed_questions.py
    11e_seed_loop_questions.py
    11f_seed_card_templates.py
    11g_seed_field_groups.py

Convención de almacenamiento:
- Campos de preguntas (forms.fields):
    code = código del campo (ej. "DES", "IMP", "VAL") o identificador único del campo.
    label = etiqueta/nombre del campo (ej. "Nombre de la innovación").
    description = descripción o enunciado del campo.
    question_id = ID de la pregunta correspondiente en forms.questions.
    field_group_id = ID del grupo de campos correspondiente en forms.field_groups (opcional).
    display_order = orden del campo dentro de la pregunta o subpregunta.
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
DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023, 2025)


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


# -----------------------------------------------------------------------------
# EXCEL
# -----------------------------------------------------------------------------


def load_fields_for_years(excel: pd.ExcelFile, years: tuple[int, ...]) -> list[dict]:
    all_fields: list[dict] = []

    for year in years:
        sheet_name = str(year)
        if sheet_name not in excel.sheet_names:
            logger.debug(f"Hoja {sheet_name!r} no encontrada. Omitiendo.")
            continue

        frame = read_sheet(excel, sheet_name)
        sheet_fields: OrderedDict[tuple[str, str], dict] = OrderedDict()

        display_order_counter = defaultdict(int)

        for idx, row in frame.iterrows():
            parent_question = clean(row.get("Pregunta")) or clean(
                row.get("COD_PREGUNTA")
            )
            subquestion = clean(row.get("Subpregunta")) or clean(
                row.get("COD_SUBPREGUNTA")
            )
            field_code = (
                clean(row.get("Codigo_Campo"))
                or clean(row.get("COD_CAMPO"))
                or clean(row.get("Campo"))
            )
            field_label = (
                clean(row.get("Nombre de la innovación"))
                or clean(row.get("Etiqueta"))
                or clean(row.get("DESCRIPCION_CAMPO"))
                or field_code
            )
            field_description = (
                clean(row.get("DESCRIPCION"))
                or clean(row.get("Enunciado"))
                or field_label
            )

            # Skip pure container rows (e.g. Row 1 of Pregunta 28 where field_code and subquestion are None)
            if parent_question is None or (field_code is None and subquestion is None):
                continue

            # Determine associated question label (Subquestion takes precedence if present)
            target_question_label = subquestion or parent_question

            # Fallback code generation if field_code isn't explicitly defined
            code = field_code or f"FIELD_{idx + 1}"

            display_order_counter[target_question_label] += 1
            display_order = display_order_counter[target_question_label]

            candidate = {
                "year": year,
                "parent_question": parent_question,
                "target_question_label": target_question_label,
                "code": code,
                "label": field_label or code,
                "description": field_description or field_label or code,
                "display_order": display_order,
            }

            key = (target_question_label, code)
            if key not in sheet_fields:
                sheet_fields[key] = candidate

        all_fields.extend(sheet_fields.values())

    return all_fields


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


async def get_forms(conn, years: tuple[int, ...]) -> dict[int, str]:
    result = await conn.execute(
        text("SELECT code, id::text AS id FROM forms.forms ORDER BY code;")
    )

    grouped: dict[int, list[str]] = defaultdict(list)
    for row in result.mappings().all():
        try:
            year = int(row["code"])
            if year in years:
                grouped[year].append(row["id"])
        except ValueError:
            continue

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


async def get_questions(
    conn,
    years: tuple[int, ...],
) -> dict[tuple[int, str], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                section.form_id::text AS form_id,
                question.label,
                question.description,
                question.display_order,
                form.code
            FROM forms.questions question
            JOIN forms.sections section ON question.section_id = section.id
            JOIN forms.forms form ON form.id = section.form_id
            ORDER BY form.code, question.label, question.id;
            """
        )
    )

    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        try:
            year = int(row["code"])
            if year in years:
                grouped[(year, normalize(row["label"]))].append(dict(row))
        except ValueError:
            continue

    lookup: dict[tuple[int, str], dict] = {}
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


async def get_field_groups(conn) -> dict[str, str]:
    """
    Map question_id to field_group_id for questions that belong to a loop/card_template.
    """
    result = await conn.execute(
        text(
            """
            SELECT
                fg.id::text AS field_group_id,
                ct.question_id::text AS question_id
            FROM forms.field_groups fg
            JOIN forms.card_templates ct ON fg.card_template_id = ct.id;
            """
        )
    )

    lookup: dict[str, str] = {}
    for row in result.mappings().all():
        lookup[row["question_id"]] = row["field_group_id"]

    return lookup


async def get_existing_fields(conn) -> dict[tuple[str, str], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                f.id::text AS field_id,
                f.question_id::text AS question_id,
                f.field_group_id::text AS field_group_id,
                f.code,
                f.label,
                f.description,
                f.display_order
            FROM forms.fields f
            ORDER BY f.question_id, f.code, f.id;
            """
        )
    )

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        key = (row["question_id"], normalize(row["code"]))
        grouped[key].append(dict(row))

    lookup: dict[tuple[str, str], dict] = {}
    for key, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                f"fields duplicados para {key}: {[row['field_id'] for row in rows]}"
            )
        if not is_uuidv7(rows[0]["field_id"]):
            raise ValueError(f"field sin UUIDv7: {rows[0]['field_id']}")
        lookup[key] = rows[0]

    return lookup


async def save_field(
    conn, record: dict, update: bool, has_field_group_col: bool
) -> None:
    if update:
        if has_field_group_col:
            statement = text(
                """
                UPDATE forms.fields
                SET
                    question_id = CAST(:question_id AS uuid),
                    field_group_id = CAST(:field_group_id AS uuid),
                    code = :code,
                    label = :label,
                    description = :description,
                    display_order = :display_order,
                    updated_at = NOW()
                WHERE id = CAST(:id AS uuid);
                """
            )
        else:
            statement = text(
                """
                UPDATE forms.fields
                SET
                    question_id = CAST(:question_id AS uuid),
                    code = :code,
                    label = :label,
                    description = :description,
                    display_order = :display_order,
                    updated_at = NOW()
                WHERE id = CAST(:id AS uuid);
                """
            )
    else:
        if has_field_group_col:
            statement = text(
                """
                INSERT INTO forms.fields (
                    id,
                    question_id,
                    field_group_id,
                    code,
                    label,
                    description,
                    display_order,
                    updated_at
                )
                VALUES (
                    CAST(:id AS uuid),
                    CAST(:question_id AS uuid),
                    CAST(:field_group_id AS uuid),
                    :code,
                    :label,
                    :description,
                    :display_order,
                    NOW()
                );
                """
            )
        else:
            statement = text(
                """
                INSERT INTO forms.fields (
                    id,
                    question_id,
                    code,
                    label,
                    description,
                    display_order,
                    updated_at
                )
                VALUES (
                    CAST(:id AS uuid),
                    CAST(:question_id AS uuid),
                    :code,
                    :label,
                    :description,
                    :display_order,
                    NOW()
                );
                """
            )

    await conn.execute(statement, record)


# -----------------------------------------------------------------------------
# CONSTRUCCIÓN Y VALIDACIÓN
# -----------------------------------------------------------------------------


def build_expected_fields(
    raw_fields: list[dict],
    questions: dict[tuple[int, str], dict],
    field_groups: dict[str, str],
) -> list[dict]:
    records: list[dict] = []

    for item in raw_fields:
        year = item["year"]
        q_label = item["target_question_label"]

        question = questions.get((year, normalize(q_label)))
        if question is None:
            raise ValueError(
                f"No existe pregunta '{q_label}' ({year}) en forms.questions."
            )

        question_id = question["question_id"]
        field_group_id = field_groups.get(question_id)

        records.append(
            {
                "natural_key": (question_id, normalize(item["code"])),
                "question_id": question_id,
                "field_group_id": field_group_id,
                "code": item["code"],
                "label": item["label"],
                "description": item["description"],
                "display_order": item["display_order"],
            }
        )

    keys = [record["natural_key"] for record in records]
    if len(keys) != len(set(keys)):
        raise ValueError("La construcción de forms.fields produjo duplicados.")

    return records


async def validate_loaded(
    conn,
    expected: list[dict],
) -> None:
    existing = await get_existing_fields(conn)

    for source in expected:
        row = existing.get(source["natural_key"])
        if row is None:
            raise ValueError(f"No se cargó field para {source['natural_key']}.")
        if row["question_id"] != source["question_id"]:
            raise ValueError(f"question_id incorrecto para {source['natural_key']}.")
        if normalize(row["code"]) != normalize(source["code"]):
            raise ValueError(f"code incorrecto para {source['natural_key']}.")
        if normalize(row["label"]) != normalize(source["label"]):
            raise ValueError(f"label incorrecto para {source['natural_key']}.")
        if not is_uuidv7(row["field_id"]):
            raise ValueError(f"UUID no es versión 7 para {source['natural_key']}.")

    logger.debug(f"forms.fields validation passed. Validated: {len(expected)}.")


# -----------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:

    path = Path(FILE_PATH)
    years = active_years()
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    logger.debug(f"Starting forms.fields population from {path}")

    excel = pd.ExcelFile(path)
    raw_fields = load_fields_for_years(excel, years)

    async with async_engine.begin() as conn:
        columns = await table_columns(conn, "forms", "fields")
        required = {
            "id",
            "question_id",
            "code",
            "label",
            "description",
            "display_order",
            "updated_at",
        }
        missing = required - set(columns)
        if missing:
            raise ValueError(f"Faltan columnas en forms.fields: {sorted(missing)}")

        has_field_group_col = "field_group_id" in columns

        questions = await get_questions(conn, years)
        field_groups = await get_field_groups(conn)
        existing = await get_existing_fields(conn)

        expected = build_expected_fields(
            raw_fields,
            questions,
            field_groups,
        )

        inserted = 0
        updated = 0

        for source in expected:
            old = existing.get(source["natural_key"])
            field_id = old["field_id"] if old else new_uuidv7()
            if not is_uuidv7(field_id):
                raise ValueError(f"ID no UUIDv7: {field_id}")

            db_record = {
                "id": field_id,
                "question_id": source["question_id"],
                "code": truncate(source["code"], columns["code"]["max_length"]),
                "label": truncate(source["label"], columns["label"]["max_length"]),
                "description": truncate(
                    source["description"],
                    columns["description"]["max_length"],
                ),
                "display_order": int(source["display_order"]),
            }

            if has_field_group_col:
                db_record["field_group_id"] = source["field_group_id"]

            await save_field(
                conn,
                db_record,
                update=old is not None,
                has_field_group_col=has_field_group_col,
            )

            if old:
                updated += 1
            else:
                inserted += 1

        await validate_loaded(conn, expected)

    logger.debug(
        "forms.fields population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}. "
        f"Expected: {len(expected)}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
