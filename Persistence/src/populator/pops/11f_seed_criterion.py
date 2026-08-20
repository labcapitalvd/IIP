"""Poblado de grading.criteria desde Estructura_IIP.xlsx.

Convención de almacenamiento:
- code:
    2023_CRIT_Q1, 2023_CRIT_ACU_ADM_COD, etc.
- label:
    Criterio General Q1, Criterio Bucle ACU_ADM_COD, etc.
- weight:
    Default 1.00 (Decimal(5, 2))
- max_score:
    Max_subpregunta_bucle / Maxb para bucles, o Maxp / Maxi para preguntas generales.
- description:
    desc b1 o Subpregunta_bucle para bucles; desc g1 o Pregunta 2023 para generales.

El script es idempotente y conserva los UUIDv7 existentes.
"""

from __future__ import annotations

import asyncio
import os
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional, cast
from uuid import UUID

import pandas as pd
from shared.infrastructure import async_engine
from shared.utils.logger import get_logger
from sqlalchemy import text
from uuid_utils import uuid7

logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------

LOCAL_IIP_STRUCTURE_FILE = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023, 2025)


# -----------------------------------------------------------------------------
# UTILIDADES
# -----------------------------------------------------------------------------


def sanitize_code_part(value: Any) -> str:
    text_val = clean_text(value) or ""
    return re.sub(r"[^A-Za-z0-9_]+", "_", text_val).strip("_")


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


def clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    value = str(value).strip()
    return value or None


def normalize_key(value: Any) -> Optional[str]:
    value = clean_text(value)
    if value is None:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character for character in value if not unicodedata.combining(character)
    )
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_code_suffix(value: Any) -> Optional[str]:
    value = clean_text(value)
    if value is None:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)*)", value)
    if not match:
        return None
    return match.group(1).replace(".", "_").replace(",", "_")


def make_code(prefix: str, raw_code: Any) -> str:
    suffix = extract_code_suffix(raw_code)
    if suffix:
        return f"{prefix}{suffix}"
    normalized = normalize_key(raw_code) or "sin_codigo"
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return f"{prefix}{normalized}"


def is_uuidv7(value: Any) -> bool:
    value = clean_text(value)
    if value is None:
        return False
    try:
        return UUID(value).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    return str(uuid7())


def truncate_text(value: Any, max_length: Optional[int]) -> Optional[str]:
    value = clean_text(value)
    if value is None or max_length is None:
        return value
    return value[:max_length]


# -----------------------------------------------------------------------------
# LECTURA Y NORMALIZACIÓN DEL EXCEL
# -----------------------------------------------------------------------------


def read_structure_sheet(excel_file: pd.ExcelFile, year: int) -> pd.DataFrame:
    sheet_name = str(year)
    if sheet_name not in excel_file.sheet_names:
        raise ValueError(
            f"No existe la hoja obligatoria {sheet_name!r}. "
            f"Hojas disponibles: {excel_file.sheet_names}"
        )
    df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=object)
    df.columns = [str(column).strip() for column in df.columns]
    return df


def build_criteria_records(df: pd.DataFrame, year: int) -> list[dict]:
    registry = OrderedDict()

    for idx, row in df.iterrows():
        source_row = cast(int, idx) + 2
        q_raw = clean_text(row.get("Pregunta"))
        if not q_raw:
            continue

        q_code = make_code("Q", q_raw)
        is_loop = clean_text(row.get("Bucle")) is not None
        # group_code = sanitize_code_part(row.get("code_field_groups"))
        field_code = sanitize_code_part(row.get("code_field"))

        if is_loop and field_code:
            # Subpregunta )de bucle: iterar sobre b1..b5
            for i in range(1, 6):
                raw_val = row.get(f"b{i}")
                desc_val = clean_text(row.get(f"desc b{i}"))

                try:
                    weight_val = (
                        float(raw_val)
                        if raw_val is not None and not pd.isna(raw_val)
                        else 0.0
                    )
                except (ValueError, TypeError):
                    weight_val = 0.0

                if weight_val > 0 or desc_val:
                    crit_code = f"{year}_CRIT_{q_code}_{field_code}_B{i}"
                    label = f"Criterio Bucle {q_code} {field_code} B{i}"
                    description = (
                        desc_val or clean_text(row.get("Subpregunta_bucle")) or label
                    )

                    key = (year, crit_code)
                    if key not in registry:
                        registry[key] = {
                            "year": year,
                            "source_row": source_row,
                            "question_code": q_code,
                            "code": crit_code,
                            "label": label,
                            "weight": weight_val,  # Real scalar score weight (e.g. 1.20, 1.60)
                            "display_order": i,
                            "max_score": 5.0,  # Max rating scale for grader UI
                            "description": description,
                        }
        else:
            # Pregunta general (non-loop): iterar sobre g1..g5
            for i in range(1, 6):
                raw_val = row.get(f"g{i}")
                desc_val = clean_text(row.get(f"desc g{i}"))

                try:
                    weight_val = (
                        float(raw_val)
                        if raw_val is not None and not pd.isna(raw_val)
                        else 0.0
                    )
                except (ValueError, TypeError):
                    weight_val = 0.0

                if weight_val > 0 or desc_val:
                    crit_code = f"{year}_CRIT_{q_code}_G{i}"
                    label = f"Criterio General {q_code} G{i}"
                    description = (
                        desc_val
                        or clean_text(row.get(f"Pregunta {year}"))
                        or clean_text(row.get("Pregunta 2023"))
                        or label
                    )

                    key = (year, crit_code)
                    if key not in registry:
                        registry[key] = {
                            "year": year,
                            "source_row": source_row,
                            "question_code": q_code,
                            "code": crit_code,
                            "label": label,
                            "weight": weight_val,  # Real scalar score weight (e.g. 1.20, 1.60)
                            "display_order": i,
                            "max_score": 5.0,  # Max rating scale for grader UI
                            "description": description,
                        }

    return list(registry.values())


# -----------------------------------------------------------------------------
# METADATOS DE BD Y LOOKUPS
# -----------------------------------------------------------------------------


async def get_table_columns(conn) -> dict:
    result = await conn.execute(
        text(
            """
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'grading' AND table_name = 'criteria'
            ORDER BY ordinal_position;
            """
        )
    )
    rows = result.mappings().all()
    if not rows:
        raise ValueError("No se encontró la tabla grading.criteria.")
    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


async def get_questions_lookup(
    conn, active_years: tuple[int, ...]
) -> dict[tuple[int, str], str]:
    result = await conn.execute(
        text(
            """
            SELECT q.code AS q_code, q.id::text AS q_id, f.code AS year_code
            FROM forms.questions q
            JOIN forms.sections s ON s.id = q.section_id
            JOIN forms.forms f ON f.id = s.form_id;
            """
        )
    )
    lookup = {}
    for row in result.mappings().all():
        try:
            year = int(row["year_code"])
            if year in active_years:
                lookup[(year, row["q_code"])] = row["q_id"]
        except (ValueError, TypeError):
            continue
    return lookup


async def get_existing_criteria(conn) -> list[dict]:
    result = await conn.execute(
        text(
            """
            SELECT id::text AS id, question_id::text AS question_id, code, label, description, weight, display_order, max_score
            FROM grading.criteria;
            """
        )
    )
    return [dict(row) for row in result.mappings().all()]


# -----------------------------------------------------------------------------
# PERSISTENCIA (INSERT / UPDATE)
# -----------------------------------------------------------------------------


def prepare_db_record(
    source_record: dict,
    db_columns: dict,
    question_id: str,
    existing_id: Optional[str],
) -> dict:
    code = truncate_text(
        source_record["code"], db_columns.get("code", {}).get("max_length")
    )
    label = truncate_text(
        source_record["label"], db_columns.get("label", {}).get("max_length")
    )
    description = truncate_text(
        source_record["description"],
        db_columns.get("description", {}).get("max_length"),
    )

    crit_id = existing_id or new_uuidv7()
    if not is_uuidv7(crit_id):
        raise ValueError(f"ID inválido para criterio {code}: {crit_id}")

    return {
        "id": crit_id,
        "question_id": question_id,
        "code": code,
        "label": label,
        "description": description,
        "weight": source_record["weight"],
        "display_order": int(source_record.get("display_order") or 999),
        "max_score": source_record["max_score"],
    }


async def insert_criterion(conn, record: dict) -> None:
    await conn.execute(
        text(
            """
            INSERT INTO grading.criteria (
                id, question_id, code, label, description, weight, display_order, max_score
            ) VALUES (
                CAST(:id AS uuid), CAST(:question_id AS uuid), :code, :label, :description, :weight, :display_order, :max_score
            );
            """
        ),
        record,
    )


async def update_criterion(conn, record: dict) -> None:
    await conn.execute(
        text(
            """
            UPDATE grading.criteria
            SET question_id = CAST(:question_id AS uuid),
                label = :label,
                description = :description,
                weight = :weight,
                display_order = :display_order,
                max_score = :max_score
            WHERE id = CAST(:id AS uuid);
            """
        ),
        record,
    )


# -----------------------------------------------------------------------------
# PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(LOCAL_IIP_STRUCTURE_FILE)
    active_years = get_active_years()

    logger.debug("Iniciando la carga de grading.criteria...")
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo local: {path}")

    excel_file = pd.ExcelFile(path)
    all_records: list[dict] = []

    for year in active_years:
        df_year = read_structure_sheet(excel_file, year)
        year_records = build_criteria_records(df_year, year)
        all_records.extend(year_records)

    async with async_engine.begin() as conn:
        db_columns = await get_table_columns(conn)
        questions_lookup = await get_questions_lookup(conn, active_years)
        existing_rows = await get_existing_criteria(conn)

        existing_by_code = {row["code"]: row for row in existing_rows}

        inserted = 0
        updated = 0

        for record in all_records:
            year = record["year"]
            q_code = record["question_code"]
            db_q_code = f"{year}_{q_code}"
            q_key = (year, db_q_code)

            question_id = questions_lookup.get(q_key)
            if not question_id:
                logger.warning(
                    f"Fila {record['source_row']}: Pregunta '{q_code}' no encontrada para el año {year}. "
                    f"Omitiendo criterio '{record['code']}'."
                )
                continue

            existing_row = existing_by_code.get(record["code"])
            existing_id = existing_row["id"] if existing_row else None

            db_record = prepare_db_record(
                source_record=record,
                db_columns=db_columns,
                question_id=question_id,
                existing_id=existing_id,
            )

            if existing_id:
                await update_criterion(conn, db_record)
                updated += 1
            else:
                await insert_criterion(conn, db_record)
                inserted += 1

    logger.debug(
        "Poblado de grading.criteria finalizado con éxito. "
        f"Insertados: {inserted}. Actualizados: {updated}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
