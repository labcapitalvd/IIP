"""Puebla forms.field_groups para los IIP 2019, 2021 y 2023.

Dependencias previas:
    11d_seed_questions.py
    11e_seed_loop_questions.py
    11f_seed_card_templates.py

Convención de almacenamiento:
- Grupo directo:
    label = código de la pregunta principal.
    description = enunciado completo de la pregunta principal.
    card_template_id = NULL.
    display_order = 1.
- Grupo repetible:
    label = código de la pregunta de bucle.
    description = enunciado completo del bucle.
    card_template_id = plantilla correspondiente.
    display_order = 2 cuando la pregunta también tiene grupo directo; 1 en
    los demás casos.

La tabla no tiene helper. No se almacenan ponderaciones ni textos técnicos.
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

from shared.db import async_engine
from shared.utils.logger import get_logger


logger = get_logger("pop/field_groups")

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)
DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023)
YEAR_WITH_LOOPS = 2023
EXPECTED_DIRECT_COUNTS = {2019: 43, 2021: 52, 2023: 39}
EXPECTED_CARD_COUNT = 27


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


def load_structure(
    excel: pd.ExcelFile,
    years: tuple[int, ...],
) -> tuple[dict[int, OrderedDict[str, str]], OrderedDict[str, dict]]:
    main_questions: dict[int, OrderedDict[str, str]] = {}

    for year in years:
        frame = read_sheet(excel, str(year))
        required = {"Pregunta", f"Pregunta {year}"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"Faltan columnas en la hoja {year}: {sorted(missing)}")

        registry: OrderedDict[str, str] = OrderedDict()
        for _, row in frame.iterrows():
            question = clean(row["Pregunta"])
            description = clean(row[f"Pregunta {year}"])
            if question is None or description is None:
                continue

            old = registry.get(question)
            if old is not None and normalize(old) != normalize(description):
                raise ValueError(f"Textos contradictorios para {question} en {year}.")
            registry.setdefault(question, description)

        if not registry:
            raise ValueError(f"La hoja {year} no produjo preguntas.")
        main_questions[year] = registry

    frame_2023 = read_sheet(excel, str(YEAR_WITH_LOOPS))
    required_loops = {"Pregunta", "Bucle", "Bucle 2023"}
    missing = required_loops - set(frame_2023.columns)
    if missing:
        raise ValueError(f"Faltan columnas de bucle en 2023: {sorted(missing)}")

    loops: OrderedDict[str, dict] = OrderedDict()
    for _, row in frame_2023.iterrows():
        loop_question = clean(row["Bucle"])
        loop_text = clean(row["Bucle 2023"])
        parent_question = clean(row["Pregunta"])
        if loop_question is None:
            continue
        if loop_text is None or parent_question is None:
            raise ValueError(f"Bucle incompleto: {loop_question}")

        old = loops.get(loop_question)
        candidate = {
            "loop_question": loop_question,
            "loop_text": loop_text,
            "parent_question": parent_question,
            "is_mixed": loop_question == parent_question,
        }
        if old is None:
            loops[loop_question] = candidate
        elif normalize(old["loop_text"]) != normalize(loop_text) or normalize(
            old["parent_question"]
        ) != normalize(parent_question):
            raise ValueError(f"Información contradictoria para {loop_question}.")

    if len(loops) != EXPECTED_CARD_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_CARD_COUNT} bucles y se encontraron {len(loops)}."
        )

    return main_questions, loops


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


async def get_questions(
    conn,
    years: tuple[int, ...],
) -> dict[tuple[int, str], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                question.form_id::text AS form_id,
                question.label,
                question.description,
                question.display_order,
                question.is_loop,
                form.anno
            FROM forms.questions question
            JOIN forms.sections section ON question.section_id = section.id
            JOIN forms.forms form ON form.id = section.form_id
            ORDER BY form.anno, question.label, question.id;
            """
        )
    )

    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        year = int(row["anno"])
        if year in years:
            grouped[(year, normalize(row["label"]))].append(dict(row))

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


async def get_card_templates(conn) -> dict[str, dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                id::text AS card_template_id,
                question_id::text AS question_id,
                label,
                description
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


async def get_existing_groups(conn) -> dict[tuple[str, str | None], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                fg.id::text AS field_group_id,
                s.form_id::text AS form_id,         -- Resolving dynamically
                ct.question_id::text AS question_id, -- Resolving dynamically
                fg.card_template_id::text AS card_template_id,
                fg.label,
                fg.description,
                fg.display_order
            FROM forms.field_groups fg
            -- CHANGE HERE: Walk the relational tree up to questions and sections
            JOIN forms.card_templates ct ON fg.card_template_id = ct.id
            JOIN forms.questions q ON ct.question_id = q.id
            JOIN forms.sections s ON q.section_id = s.id
            ORDER BY ct.question_id, fg.card_template_id, fg.id;
            """
        )
    )

    grouped: dict[tuple[str, str | None], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        key = (row["question_id"], row["card_template_id"])
        grouped[key].append(dict(row))

    lookup: dict[tuple[str, str | None], dict] = {}
    for key, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                f"field_groups duplicados para {key}: "
                f"{[row['field_group_id'] for row in rows]}"
            )
        if not is_uuidv7(rows[0]["field_group_id"]):
            raise ValueError(f"field_group sin UUIDv7: {rows[0]['field_group_id']}")
        lookup[key] = rows[0]

    return lookup


async def save_group(conn, record: dict, update: bool) -> None:
    if update:
        statement = text(
            """
            UPDATE forms.field_groups
            SET
                card_template_id = CAST(:card_template_id AS uuid),
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
            INSERT INTO forms.field_groups (
                id,
                card_template_id,
                label,
                description,
                display_order,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:card_template_id AS uuid),
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


def build_expected_groups(
    main_questions: dict[int, OrderedDict[str, str]],
    loops: OrderedDict[str, dict],
    forms: dict[int, str],
    questions: dict[tuple[int, str], dict],
    templates: dict[str, dict],
) -> list[dict]:
    records: list[dict] = []

    for year, year_questions in main_questions.items():
        for question_code, question_text in year_questions.items():
            question = questions.get((year, normalize(question_code)))
            if question is None:
                raise ValueError(
                    f"No existe {year} / {question_code} en forms.questions."
                )

            records.append(
                {
                    "natural_key": (question["question_id"], None),
                    "kind": "DIRECT",
                    "year": year,
                    "form_id": forms[year],
                    "question_id": question["question_id"],
                    "card_template_id": None,
                    "label": question_code,
                    "description": question_text,
                    "display_order": 1,
                }
            )

    for loop_code, loop in loops.items():
        question = questions.get((YEAR_WITH_LOOPS, normalize(loop_code)))
        if question is None:
            raise ValueError(f"No existe {loop_code} en forms.questions.")
        if question["is_loop"] is not True:
            raise ValueError(f"{loop_code} tiene is_loop distinto de TRUE.")

        template = templates.get(question["question_id"])
        if template is None:
            raise ValueError(
                f"No existe card_template para {loop_code}. "
                "Ejecuta antes 11f_seed_card_templates.py."
            )

        records.append(
            {
                "natural_key": (
                    question["question_id"],
                    template["card_template_id"],
                ),
                "kind": "CARD",
                "year": YEAR_WITH_LOOPS,
                "form_id": forms[YEAR_WITH_LOOPS],
                "question_id": question["question_id"],
                "card_template_id": template["card_template_id"],
                "label": loop_code,
                "description": loop["loop_text"],
                "display_order": 2 if loop["is_mixed"] else 1,
            }
        )

    keys = [record["natural_key"] for record in records]
    if len(keys) != len(set(keys)):
        raise ValueError("La construcción de field_groups produjo duplicados.")

    direct_counts = defaultdict(int)
    card_count = 0
    for record in records:
        if record["kind"] == "DIRECT":
            direct_counts[record["year"]] += 1
        else:
            card_count += 1

    expected_direct = {year: EXPECTED_DIRECT_COUNTS[year] for year in main_questions}
    if dict(direct_counts) != expected_direct:
        raise ValueError(
            f"Conteos directos inesperados: {dict(direct_counts)}; "
            f"esperado: {expected_direct}."
        )
    if card_count != EXPECTED_CARD_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_CARD_COUNT} grupos CARD y se "
            f"construyeron {card_count}."
        )

    return records


async def validate_loaded(
    conn,
    expected: list[dict],
) -> None:
    existing = await get_existing_groups(conn)

    for source in expected:
        row = existing.get(source["natural_key"])
        if row is None:
            raise ValueError(f"No se cargó field_group para {source['natural_key']}.")
        if row["form_id"] != source["form_id"]:
            raise ValueError(f"form_id incorrecto para {source['natural_key']}.")
        if normalize(row["label"]) != normalize(source["label"]):
            raise ValueError(f"label incorrecto para {source['natural_key']}.")
        if normalize(row["description"]) != normalize(source["description"]):
            raise ValueError(f"description incorrecta para {source['natural_key']}.")
        if int(row["display_order"]) != int(source["display_order"]):
            raise ValueError(f"display_order incorrecto para {source['natural_key']}.")
        if not is_uuidv7(row["field_group_id"]):
            raise ValueError(f"UUID no es versión 7 para {source['natural_key']}.")

    logger.info(f"forms.field_groups validation passed. Validated: {len(expected)}.")


# -----------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade(gh=None, api=None) -> None:
    del gh, api

    path = Path(FILE_PATH)
    years = active_years()
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    logger.info(f"Starting forms.field_groups population from {path}")

    excel = pd.ExcelFile(path)
    main_questions, loops = load_structure(excel, years)

    async with async_engine.begin() as conn:
        columns = await table_columns(conn, "forms", "field_groups")
        required = {
            "id",
            "card_template_id",
            "label",
            "description",
            "display_order",
            "updated_at",
        }
        missing = required - set(columns)
        if missing:
            raise ValueError(
                f"Faltan columnas en forms.field_groups: {sorted(missing)}"
            )
        if not columns["card_template_id"]["nullable"]:
            raise ValueError("forms.field_groups.card_template_id debe permitir NULL.")

        forms = await get_forms(conn, years)
        questions = await get_questions(conn, years)
        templates = await get_card_templates(conn)
        existing = await get_existing_groups(conn)

        expected = build_expected_groups(
            main_questions,
            loops,
            forms,
            questions,
            templates,
        )

        inserted = 0
        updated = 0

        for source in expected:
            old = existing.get(source["natural_key"])
            field_group_id = old["field_group_id"] if old else new_uuidv7()
            if not is_uuidv7(field_group_id):
                raise ValueError(f"ID no UUIDv7: {field_group_id}")

            db_record = {
                "id": field_group_id,
                "form_id": source["form_id"],
                "question_id": source["question_id"],
                "card_template_id": source["card_template_id"],
                "label": truncate(source["label"], columns["label"]["max_length"]),
                "description": truncate(
                    source["description"],
                    columns["description"]["max_length"],
                ),
                "display_order": int(source["display_order"]),
            }

            await save_group(conn, db_record, update=old is not None)
            if old:
                updated += 1
            else:
                inserted += 1

        await validate_loaded(conn, expected)

    logger.info(
        "forms.field_groups population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}. "
        f"Expected: {len(expected)}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
