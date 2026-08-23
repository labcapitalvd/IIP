"""Poblado de grading.criteria desde Estructura_IIP.xlsx.

Convención de almacenamiento:
- code: 2023_CRIT_Q1, 2023_CRIT_ACU_ADM_COD, etc.
- label: Criterio General Q1, Criterio Bucle ACU_ADM_COD, etc.
- weight: Ponderación escalar (Decimal(5, 2))
- max_score: Escala de puntuación máxima para el calificador (Default: 5.0)
- description: Detalle del criterio descriptivo tomado del Excel.

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva los UUIDv7 existentes de forma transparente.
"""

import asyncio
import os
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, cast

import pandas as pd

# Infraestructura y Registro global del proyecto
from shared.infrastructure import async_engine

# Importación de Modelos ORM Centralizados desde tu Módulo init
from shared.models import Criterion, Form, Question, Section
from shared.utils.logger import get_logger

# Utilidades Core de Seeding Compartidas (Elimina duplicación)
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_no_duplicates,
    clean_text,
    extract_numeric_suffix,
    fold_for_comparison,
    get_seeding_active_years,
    get_table_columns,
    load_clean_excel_sheet,
    new_uuidv7,
    truncate_text,
    validate_required_columns,
)
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN ESPECÍFICA DE ÁMBITO
# -----------------------------------------------------------------------------

LOCAL_IIP_STRUCTURE_FILE = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

# -----------------------------------------------------------------------------
# IDENTIFICADORES TÉCNICOS Y TRATAMIENTO LOCAL
# -----------------------------------------------------------------------------


def sanitize_code_part_local(value: Any) -> str:
    text_val = clean_text(value) or ""
    return re.sub(r"[^A-Za-z0-9_]+", "_", text_val).strip("_")


def make_code_local(prefix: str, raw_code: Any) -> str:
    suffix = extract_numeric_suffix(raw_code)
    if suffix:
        return f"{prefix}{suffix}"
    folded = fold_for_comparison(raw_code) or "sin_codigo"
    cleaned = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
    return f"{prefix}{cleaned}"


# -----------------------------------------------------------------------------
# ETL Y EXTRACCIÓN DESDE EL LIBRO EXCEL
# -----------------------------------------------------------------------------


def build_criteria_records(df: pd.DataFrame, year: int) -> list[dict]:
    registry = OrderedDict()

    for idx, row in df.iterrows():
        source_row = cast(int, idx) + 2
        q_raw = clean_text(row.get("Pregunta"))
        if not q_raw:
            continue

        q_code = make_code_local("Q", q_raw)
        is_loop = clean_text(row.get("Bucle")) is not None
        field_code = sanitize_code_part_local(row.get("code_field"))

        if is_loop and field_code:
            # Subpregunta de bucle: iterar sobre las ponderaciones de b1..b5
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
                            "weight": weight_val,
                            "display_order": i,
                            "max_score": 5.0,
                            "description": description,
                        }
        else:
            # Pregunta general estándar: iterar sobre las ponderaciones de g1..g5
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
                            "weight": weight_val,
                            "display_order": i,
                            "max_score": 5.0,
                            "description": description,
                        }

    return list(registry.values())


# -----------------------------------------------------------------------------
# LOOKUPS CENTRALIZADOS VÍA ORM
# -----------------------------------------------------------------------------


async def get_questions_lookup(
    conn: AsyncConnection, active_years: tuple[int, ...]
) -> dict[tuple[int, str], str]:
    stmt = (
        select(
            Question.code.label("q_code"),
            Question.id.label("q_id"),
            Form.code.label("form_year"),
        )
        .join(Section, Section.id == Question.section_id)
        .join(Form, Form.id == Section.form_id)
    )
    result = await conn.execute(stmt)

    lookup: dict[tuple[int, str], str] = {}
    for row in result.mappings().all():
        try:
            year = int(row["form_year"])
            if year in active_years:
                lookup[(year, str(row["q_code"]))] = str(row["q_id"])
        except (ValueError, TypeError):
            continue
    return lookup


async def get_existing_criteria(conn: AsyncConnection) -> list[dict]:
    stmt = select(
        Criterion.id,
        Criterion.question_id,
        Criterion.code,
        Criterion.label,
        Criterion.description,
        Criterion.weight,
        Criterion.display_order,
        Criterion.max_score,
    )
    rows = (await conn.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


# -----------------------------------------------------------------------------
# EJECUCIÓN CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(LOCAL_IIP_STRUCTURE_FILE)
    active_years = get_seeding_active_years()

    logger.debug("Iniciando la ejecución de poblado para grading.criteria...")
    if not path.exists():
        raise FileNotFoundError(f"Archivo de origen Excel no encontrado: {path}")

    try:
        excel_file = pd.ExcelFile(path)
        all_records: list[dict] = []

        # ETL del libro Excel por año operacional activo
        for year in active_years:
            df_year = load_clean_excel_sheet(
                excel_file, sheet_name=str(year), required_columns={"Pregunta"}
            )
            year_records = build_criteria_records(df_year, year)
            all_records.extend(year_records)

        async with async_engine.begin() as conn:
            # Validación e introspección dinámica de las columnas físicas reales de la tabla
            db_columns = await get_table_columns(
                conn, schema="grading", table="criteria"
            )
            validate_required_columns(
                db_columns,
                required={
                    "id",
                    "question_id",
                    "code",
                    "label",
                    "description",
                    "weight",
                    "display_order",
                    "max_score",
                },
                table_name="grading.criteria",
            )

            # Obtención de mapeos relacionales estables
            questions_lookup = await get_questions_lookup(conn, active_years)
            existing_rows = await get_existing_criteria(conn)
            existing_by_code = {str(row["code"]): row for row in existing_rows}

            inserted = 0
            updated = 0

            for record in all_records:
                year = record["year"]
                q_code = record["question_code"]
                db_q_code = f"{year}_{q_code}"
                q_key = (year, db_q_code)

                # Resolver el ID relacional de la pregunta mapeada previamente
                question_id = questions_lookup.get(q_key)
                if not question_id:
                    logger.warning(
                        f"Fila {record['source_row']}: Pregunta '{q_code}' no encontrada para el año {year} en la BD. "
                        f"Omitiendo criterio '{record['code']}'."
                    )
                    continue

                existing_row = existing_by_code.get(record["code"])
                existing_id = str(existing_row["id"]) if existing_row else None

                # Garantizar identificador primario idempotente UUIDv7
                crit_id = existing_id or new_uuidv7()

                db_payload = {
                    "id": crit_id,
                    "question_id": question_id,
                    "code": truncate_text(
                        record["code"], db_columns.get("code", {}).get("max_length")
                    ),
                    "label": truncate_text(
                        record["label"], db_columns.get("label", {}).get("max_length")
                    ),
                    "description": truncate_text(
                        record["description"],
                        db_columns.get("description", {}).get("max_length"),
                    ),
                    "weight": record["weight"],
                    "display_order": int(record.get("display_order") or 999),
                    "max_score": record["max_score"],
                }

                if existing_id:
                    stmt_update = (
                        update(Criterion)
                        .where(Criterion.id == db_payload["id"])
                        .values(
                            question_id=db_payload["question_id"],
                            code=db_payload["code"],
                            label=db_payload["label"],
                            description=db_payload["description"],
                            weight=db_payload["weight"],
                            display_order=db_payload["display_order"],
                            max_score=db_payload["max_score"],
                        )
                    )
                    await conn.execute(stmt_update)
                    updated += 1
                else:
                    stmt_insert = insert(Criterion).values(db_payload)
                    await conn.execute(stmt_insert)
                    inserted += 1

            # -----------------------------------------------------------------------------
            # ASERCIONES FINALES DE SANIDAD POST-CARGA CENTRALIZADA
            # -----------------------------------------------------------------------------
            final_stmt = select(Criterion.id, Criterion.code)
            final_rows = [
                dict(r) for r in (await conn.execute(final_stmt)).mappings().all()
            ]

            assert_all_uuidv7(rows=final_rows, id_key="id", label_key="code")
            assert_no_duplicates(
                rows=final_rows, key_fields=["code"], what="criterios de evaluación"
            )

        logger.info(
            f"Poblado de grading.criteria finalizado con éxito. Insertados: {inserted}. Actualizados: {updated}."
        )

    except Exception as exc:
        logger.error(f"Error crítico en el proceso de poblado de criteria: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(upgrade())
