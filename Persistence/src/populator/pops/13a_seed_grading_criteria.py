"""Puebla grading.criteria con los pesos de las preguntas del IIP.

Dependencias previas:
    11d_seed_questions.py
    11e_seed_loop_questions.py

Fuente:
    Estructura_IIP.xlsx

Alcance:
    - 2019
    - 2021
    - 2023

Criterios de 2019 y 2021:
    - Un criterio por cada pregunta principal.
    - El peso se toma de Maxp.

Criterios de 2023:
    - Las preguntas sin bucle independiente usan Maxp.
    - Cuando una pregunta principal tiene uno o varios bucles independientes,
      el criterio se asigna a los bucles usando Maxb y no se duplica el peso en
      la pregunta padre.
    - Pregunta 28.1 es mixta y se conserva como un único criterio.

Resultado esperado:
    2019: 43 criterios
    2021: 52 criterios
    2023: 43 criterios
    Total: 138 criterios

Decisiones:
    - No utiliza helper.
    - No guarda ponderaciones en descriptions de forms.*.
    - Conserva UUIDv7 existentes.
    - Crea UUIDv7 para registros nuevos.
    - La idempotencia se basa en question_id.
"""

from __future__ import annotations

import asyncio
import os
import re
import unicodedata
from collections import OrderedDict, defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from uuid_utils import uuid7

from shared_db import async_engine
from shared_utils.logger import get_logger


logger = get_logger("pop/grading_criteria")

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)
DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023)
EXPECTED_COUNTS = {
    2019: 43,
    2021: 52,
    2023: 43,
}


def get_active_years() -> tuple[int, ...]:
    raw = os.getenv("IIP_ACTIVE_YEARS")
    if not raw:
        return DEFAULT_ACTIVE_YEARS

    years: list[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            years.append(int(item))
        except ValueError as exc:
            raise ValueError(
                f"Año inválido en IIP_ACTIVE_YEARS: {item!r}"
            ) from exc

    if not years:
        raise ValueError("IIP_ACTIVE_YEARS no contiene años válidos.")
    if len(years) != len(set(years)):
        raise ValueError(f"IIP_ACTIVE_YEARS contiene duplicados: {years}")

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


def normalize_text(value):
    value = clean(value)
    if value is None:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )
    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_decimal(value, context: str) -> Decimal:
    value = clean(value)
    if value is None:
        raise ValueError(f"Ponderación vacía en {context}.")

    normalized = (
        value.replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(
            f"Ponderación inválida en {context}: {value!r}"
        ) from exc


def is_uuidv7(value) -> bool:
    try:
        return UUID(str(value)).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    return str(uuid7())


def truncate(value: str, max_length: int | None) -> str:
    if max_length is None:
        return value
    return value[:max_length]


def read_sheet(excel: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    if sheet_name not in excel.sheet_names:
        raise ValueError(
            f"No existe la hoja {sheet_name!r}. "
            f"Hojas disponibles: {excel.sheet_names}"
        )

    df = pd.read_excel(excel, sheet_name=sheet_name, dtype=object)
    df.columns = [str(column).strip() for column in df.columns]
    return df


def add_weight_record(
    registry: OrderedDict,
    year: int,
    question_code: str,
    weight: Decimal,
    source_kind: str,
    source_row: int,
) -> None:
    key = (year, normalize_text(question_code))
    current = registry.get(key)

    if current is None:
        registry[key] = {
            "year": year,
            "question_code": question_code,
            "weight": weight,
            "source_kinds": {source_kind},
            "source_rows": [source_row],
        }
        return

    if current["weight"] != weight:
        raise ValueError(
            f"La pregunta {question_code} de {year} tiene pesos "
            f"contradictorios: {current['weight']} y {weight}."
        )

    current["source_kinds"].add(source_kind)
    current["source_rows"].append(source_row)


def load_weight_records(
    path: Path,
    active_years: tuple[int, ...],
) -> list[dict]:
    excel = pd.ExcelFile(path)
    output: list[dict] = []

    for year in active_years:
        df = read_sheet(excel, str(year))
        required = {
            "Pregunta",
            f"Pregunta {year}",
            "Maxp",
            "Bucle",
            f"Bucle {year}",
            "Maxb",
        }
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Faltan columnas en la hoja {year}: {sorted(missing)}"
            )

        main_weights: OrderedDict[str, dict] = OrderedDict()
        loop_weights: OrderedDict[str, dict] = OrderedDict()
        children_by_parent: dict[str, set[str]] = defaultdict(set)

        for index, row in df.iterrows():
            source_row = int(index) + 2
            question_code = clean(row["Pregunta"])
            question_text = clean(row[f"Pregunta {year}"])

            if question_code and question_text:
                weight = parse_decimal(
                    row["Maxp"],
                    f"hoja {year}, {question_code}, fila {source_row}",
                )
                key = normalize_text(question_code)
                previous = main_weights.get(key)
                if previous is None:
                    main_weights[key] = {
                        "code": question_code,
                        "weight": weight,
                    }
                elif previous["weight"] != weight:
                    raise ValueError(
                        f"Maxp contradictorio para {question_code} en {year}."
                    )

            loop_code = clean(row["Bucle"])
            loop_text = clean(row[f"Bucle {year}"])

            if loop_code and loop_text:
                if not question_code:
                    raise ValueError(
                        f"Bucle {loop_code} sin pregunta padre en fila "
                        f"{source_row}."
                    )

                weight = parse_decimal(
                    row["Maxb"],
                    f"hoja {year}, {loop_code}, fila {source_row}",
                )
                loop_key = normalize_text(loop_code)
                previous = loop_weights.get(loop_key)
                if previous is None:
                    loop_weights[loop_key] = {
                        "code": loop_code,
                        "weight": weight,
                        "parent_code": question_code,
                    }
                else:
                    if previous["weight"] != weight:
                        raise ValueError(
                            f"Maxb contradictorio para {loop_code} en {year}."
                        )
                    if normalize_text(previous["parent_code"]) != normalize_text(
                        question_code
                    ):
                        raise ValueError(
                            f"El bucle {loop_code} tiene padres contradictorios."
                        )

                children_by_parent[normalize_text(question_code)].add(loop_key)

        registry: OrderedDict = OrderedDict()

        if year in (2019, 2021):
            for item in main_weights.values():
                add_weight_record(
                    registry,
                    year,
                    item["code"],
                    item["weight"],
                    "MAXP",
                    0,
                )
        else:
            # Preguntas principales sin bucles independientes.
            for main_key, item in main_weights.items():
                children = children_by_parent.get(main_key, set())
                independent_children = {
                    child
                    for child in children
                    if child != main_key
                }

                if not independent_children:
                    add_weight_record(
                        registry,
                        year,
                        item["code"],
                        item["weight"],
                        "MAXP",
                        0,
                    )

            # Cada bucle independiente es una unidad calificable con Maxb.
            # El bucle mixto se omite aquí porque ya quedó como pregunta principal.
            for loop_key, item in loop_weights.items():
                parent_key = normalize_text(item["parent_code"])
                if loop_key == parent_key:
                    main = main_weights.get(parent_key)
                    if main is None:
                        raise ValueError(
                            f"No se encontró la pregunta mixta {item['code']}."
                        )
                    if main["weight"] != item["weight"]:
                        raise ValueError(
                            f"La pregunta mixta {item['code']} tiene Maxp y "
                            "Maxb diferentes."
                        )
                    continue

                add_weight_record(
                    registry,
                    year,
                    item["code"],
                    item["weight"],
                    "MAXB",
                    0,
                )

        year_records = list(registry.values())
        expected = EXPECTED_COUNTS[year]
        if len(year_records) != expected:
            raise ValueError(
                f"Se esperaban {expected} criterios para {year} y se "
                f"construyeron {len(year_records)}."
            )

        total_weight = sum(
            record["weight"]
            for record in year_records
        )
        logger.info(
            f"Year {year}: criteria={len(year_records)}, "
            f"source_weight_sum={total_weight}."
        )

        output.extend(year_records)

    return output


async def get_table_columns(conn, schema: str, table: str) -> dict:
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
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
        raise ValueError(f"No existe la tabla {schema}.{table}.")

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "numeric_precision": row["numeric_precision"],
            "numeric_scale": row["numeric_scale"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_criteria_columns(columns: dict) -> None:
    required = {
        "id",
        "question_id",
        "description",
        "weight",
        "display_order",
    }
    missing = required - set(columns)
    if missing:
        raise ValueError(
            "La tabla grading.criteria no tiene todas las columnas "
            f"requeridas. Faltan: {sorted(missing)}"
        )


async def resolve_questions(
    conn,
    weight_records: list[dict],
    active_years: tuple[int, ...],
) -> dict[tuple[int, str], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                question.label,
                question.description,
                question.display_order,
                question.form_id::text AS form_id,
                form.anno
            FROM forms.questions question
            JOIN forms.forms form
              ON form.id = question.form_id
            ORDER BY form.anno, question.label, question.id;
            """
        )
    )

    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        year = int(row["anno"])
        if year not in active_years:
            continue
        grouped[(year, normalize_text(row["label"]))].append(dict(row))

    lookup: dict[tuple[int, str], dict] = {}
    for record in weight_records:
        key = (
            int(record["year"]),
            normalize_text(record["question_code"]),
        )
        rows = grouped.get(key, [])
        if len(rows) != 1:
            raise ValueError(
                f"No se pudo resolver forms.questions para "
                f"{record['year']} / {record['question_code']}. "
                f"Coincidencias: {len(rows)}."
            )

        question = rows[0]
        if not is_uuidv7(question["question_id"]):
            raise ValueError(
                f"question_id no UUIDv7 para {record['question_code']}: "
                f"{question['question_id']}"
            )
        if not is_uuidv7(question["form_id"]):
            raise ValueError(
                f"form_id no UUIDv7 para {record['question_code']}: "
                f"{question['form_id']}"
            )

        lookup[key] = question

    return lookup


async def get_existing_criteria(conn) -> dict[str, dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                id::text AS criterion_id,
                question_id::text AS question_id,
                description,
                weight,
                display_order
            FROM grading.criteria
            WHERE question_id IS NOT NULL
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
                f"Existen varios criterios para question_id={question_id}: "
                f"{[row['criterion_id'] for row in rows]}"
            )

        criterion_id = rows[0]["criterion_id"]
        if not is_uuidv7(criterion_id):
            raise ValueError(
                f"El criterio existente no tiene UUIDv7: {criterion_id}"
            )
        lookup[question_id] = rows[0]

    return lookup


def quantize_weight(weight: Decimal, scale: int | None) -> Decimal:
    if scale is None:
        return weight
    quantum = Decimal(1).scaleb(-int(scale))
    return weight.quantize(quantum, rounding=ROUND_HALF_UP)


async def save_criterion(conn, record: dict, update: bool) -> None:
    if update:
        statement = text(
            """
            UPDATE grading.criteria
            SET
                question_id = CAST(:question_id AS uuid),
                description = :description,
                weight = :weight,
                display_order = :display_order
            WHERE id = CAST(:id AS uuid);
            """
        )
    else:
        statement = text(
            """
            INSERT INTO grading.criteria (
                id,
                question_id,
                description,
                weight,
                display_order
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:question_id AS uuid),
                :description,
                :weight,
                :display_order
            );
            """
        )

    await conn.execute(statement, record)


async def persist_criteria(
    conn,
    weight_records: list[dict],
    questions: dict[tuple[int, str], dict],
    columns: dict,
) -> tuple[int, int, list[dict]]:
    existing = await get_existing_criteria(conn)
    scale = columns["weight"]["numeric_scale"]

    inserted = 0
    updated = 0
    expected_records: list[dict] = []

    for source in weight_records:
        key = (
            int(source["year"]),
            normalize_text(source["question_code"]),
        )
        question = questions[key]
        question_id = question["question_id"]
        old = existing.get(question_id)

        criterion_id = (
            old["criterion_id"]
            if old is not None
            else new_uuidv7()
        )
        if not is_uuidv7(criterion_id):
            raise ValueError(
                f"El ID preparado para criterio no es UUIDv7: {criterion_id}"
            )

        source_weight = source["weight"]
        stored_weight = quantize_weight(source_weight, scale)
        if stored_weight != source_weight:
            logger.warning(
                f"El peso de {source['year']} / "
                f"{source['question_code']} se ajustará de "
                f"{source_weight} a {stored_weight} porque "
                f"grading.criteria.weight tiene escala {scale}."
            )

        description = clean(question["description"]) or source["question_code"]
        description = truncate(
            description,
            columns["description"]["max_length"],
        )

        record = {
            "id": criterion_id,
            "question_id": question_id,
            "description": description,
            "weight": stored_weight,
            "display_order": int(question["display_order"] or 0),
            "year": int(source["year"]),
            "question_code": source["question_code"],
        }

        await save_criterion(conn, record, update=old is not None)

        if old is None:
            inserted += 1
        else:
            updated += 1

        expected_records.append(record)

    return inserted, updated, expected_records


async def validate_loaded_criteria(
    conn,
    expected_records: list[dict],
    active_years: tuple[int, ...],
) -> None:
    expected_by_question = {
        record["question_id"]: record
        for record in expected_records
    }

    result = await conn.execute(
        text(
            """
            SELECT
                criterion.id::text AS criterion_id,
                criterion.question_id::text AS question_id,
                criterion.description,
                criterion.weight,
                criterion.display_order,
                form.anno
            FROM grading.criteria criterion
            JOIN forms.questions question
              ON question.id = criterion.question_id
            JOIN forms.forms form
              ON form.id = question.form_id
            WHERE criterion.question_id IS NOT NULL
            ORDER BY form.anno, criterion.question_id;
            """
        )
    )

    loaded: dict[str, dict] = {}
    for row in result.mappings().all():
        year = int(row["anno"])
        if year not in active_years:
            continue
        question_id = row["question_id"]
        if question_id not in expected_by_question:
            continue
        if question_id in loaded:
            raise ValueError(
                f"El criterio de la pregunta {question_id} aparece duplicado."
            )
        loaded[question_id] = dict(row)

    missing = set(expected_by_question) - set(loaded)
    if missing:
        raise ValueError(
            "No se cargaron todos los criterios esperados. "
            f"Question IDs faltantes: {sorted(missing)[:20]}"
        )

    counts: dict[int, int] = defaultdict(int)
    for question_id, expected in expected_by_question.items():
        row = loaded[question_id]

        if not is_uuidv7(row["criterion_id"]):
            raise ValueError(
                f"El criterio de {question_id} no tiene UUIDv7: "
                f"{row['criterion_id']}"
            )
        if Decimal(str(row["weight"])) != expected["weight"]:
            raise ValueError(
                f"Peso incorrecto para {question_id}: "
                f"SQL={row['weight']}; esperado={expected['weight']}."
            )
        if int(row["display_order"] or 0) != int(expected["display_order"]):
            raise ValueError(
                f"display_order incorrecto para {question_id}."
            )

        counts[int(row["anno"])] += 1

    expected_counts = {
        year: EXPECTED_COUNTS[year]
        for year in active_years
        if year in EXPECTED_COUNTS
    }
    actual_counts = {
        year: counts.get(year, 0)
        for year in expected_counts
    }

    if actual_counts != expected_counts:
        raise ValueError(
            "Validación de criterios por año falló. "
            f"Esperado={expected_counts}; obtenido={actual_counts}."
        )

    logger.info(
        "grading.criteria validation passed successfully. "
        f"Validated criteria: {len(expected_by_question)}."
    )


async def upgrade(gh=None, api=None) -> None:
    del gh, api

    path = Path(FILE_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    active_years = get_active_years()
    logger.info(
        f"Starting grading.criteria population from {path}. "
        f"Active years: {active_years}."
    )

    weight_records = load_weight_records(path, active_years)

    async with async_engine.begin() as conn:
        columns = await get_table_columns(
            conn,
            "grading",
            "criteria",
        )
        validate_criteria_columns(columns)

        questions = await resolve_questions(
            conn=conn,
            weight_records=weight_records,
            active_years=active_years,
        )

        inserted, updated, expected_records = await persist_criteria(
            conn=conn,
            weight_records=weight_records,
            questions=questions,
            columns=columns,
        )

        await validate_loaded_criteria(
            conn=conn,
            expected_records=expected_records,
            active_years=active_years,
        )

    total = len(expected_records)
    logger.info(
        "grading.criteria population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}. Total: {total}."
    )
    print(
        f"[13a] OK. Insertados={inserted}; actualizados={updated}; "
        f"total={total}.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
