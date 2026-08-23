"""Puebla las preguntas tipo bucle para cualquier año configurado en DEFAULT_ACTIVE_YEARS o IIP_ACTIVE_YEARS.

Dependencias previas:
    - seed_sections (Secciones cargadas)
    - seed_questions (Preguntas principales del formulario cargadas)

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva UUIDv7 existentes basándose en estrategias
de coincidencia por combinaciones únicas de años, etiquetas y jerarquías.
"""

import asyncio
import os
import re
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any, TypedDict

import pandas as pd
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

# Infraestructura y Registro global del proyecto
from shared.infrastructure import async_engine
from shared.utils.logger import get_logger

# Importación de Modelos ORM Centralizados desde tu Módulo init
from shared.models import Form, Question, Section, SectionType

# Utilidades Core de Seeding Compartidas (Elimina duplicación)
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_no_duplicates,
    get_seeding_active_years,
    get_table_columns,
    load_clean_excel_sheet,
    validate_required_columns,
)
from shared.utils.seeding import (
    clean_text,
    compute_hierarchical_order,
    fold_for_comparison,
    new_uuidv7,
    truncate_text,
)

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN ESPECÍFICA DE ÁMBITO
# -----------------------------------------------------------------------------

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

# -----------------------------------------------------------------------------
# ESTRUCTURAS DE TIPOS Y TRATAMIENTO LOCAL
# -----------------------------------------------------------------------------


class SubquestionDict(TypedDict):
    order: int
    text: str


class LoopRecord(TypedDict):
    year: int
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


def parse_positive_integer_local(value: Any, context: str) -> int:
    cleaned = clean_text(value)
    if cleaned is None:
        raise ValueError(f"Valor vacío en {context}.")
    try:
        numeric = float(str(cleaned).replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Valor inválido en {context}: {cleaned!r}") from exc
    if not numeric.is_integer() or numeric <= 0:
        raise ValueError(f"Valor inválido en {context}: {cleaned!r}")
    return int(numeric)


# -----------------------------------------------------------------------------
# ETL Y EXTRACCIÓN DESDE EL LIBRO EXCEL
# -----------------------------------------------------------------------------


def load_loops_from_excel(
    excel: pd.ExcelFile, years: tuple[int, ...]
) -> list[LoopRecord]:
    all_records: list[LoopRecord] = []

    for year in years:
        sheet_name = str(year)
        if sheet_name not in excel.sheet_names:
            logger.warning(f"La hoja {year} no existe en el archivo Excel. Se omite.")
            continue

        required_cols = {
            "Componente",
            "Variable",
            "Indicador",
            "Pregunta",
            f"Pregunta {year}",
            "Bucle",
            f"Bucle {year}",
            "Orden_subpregunta_bucle",
            "Subpregunta_bucle",
        }

        # Intentar cargar usando validación de columnas limpia estructural
        try:
            frame = load_clean_excel_sheet(
                excel, sheet_name=sheet_name, required_columns=required_cols
            )
        except ValueError:
            logger.debug(
                f"Omitiendo año {year}: no contiene columnas de bucle o está incompleta."
            )
            continue

        data = pd.DataFrame(
            {
                "source_row": frame.index + 2,
                "component": frame["Componente"],
                "variable": frame["Variable"],
                "indicator": frame["Indicador"],
                "parent_question": frame["Pregunta"],
                "parent_text": frame[f"Pregunta {year}"],
                "loop_question": frame["Bucle"],
                "loop_text": frame[f"Bucle {year}"],
                "subquestion_order": frame["Orden_subpregunta_bucle"],
                "subquestion_text": frame["Subpregunta_bucle"],
            }
        )

        for col in data.columns:
            if col != "source_row":
                data[col] = data[col].apply(clean_text)

        fill_columns = [
            "component",
            "variable",
            "indicator",
            "parent_question",
            "parent_text",
        ]
        data[fill_columns] = data[fill_columns].ffill()

        data = data[
            data[
                [
                    "component",
                    "variable",
                    "indicator",
                    "parent_question",
                    "loop_question",
                    "loop_text",
                    "subquestion_text",
                ]
            ]
            .notna()
            .all(axis=1)
        ].copy()

        if data.empty:
            continue

        registry: OrderedDict[str, LoopRecord] = OrderedDict()

        for _, row in data.iterrows():
            loop_question = str(row["loop_question"])
            candidate: LoopRecord = {
                "year": year,
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
                fields_to_check = (
                    "component",
                    "variable",
                    "indicator",
                    "parent_question",
                    "loop_text",
                    "is_mixed",
                )
                conflicts = []
                for f in fields_to_check:
                    left, right = current[f], candidate[f]
                    equal = (
                        (left == right)
                        if f == "is_mixed"
                        else (fold_for_comparison(left) == fold_for_comparison(right))
                    )
                    if not equal:
                        conflicts.append(f)
                if conflicts:
                    raise ValueError(
                        f"Información contradictoria para {loop_question} en {year}. "
                        f"Campos en conflicto: {conflicts}. Fila conflicto: {candidate['source_row']}."
                    )

            order_val = parse_positive_integer_local(
                row["subquestion_order"],
                f"Orden_subpregunta_bucle ({year}), fila {int(row['source_row'])}",
            )
            text_value = row["subquestion_text"]

            subq_dict = current["subquestions"]
            if isinstance(subq_dict, OrderedDict):
                previous = subq_dict.get(order_val)
                if previous is not None and fold_for_comparison(
                    previous
                ) != fold_for_comparison(text_value):
                    raise ValueError(
                        f"Subpregunta contradictoria en {loop_question} ({year}), orden {order_val}."
                    )
                subq_dict[order_val] = text_value

        year_records = list(registry.values())
        year_records.sort(
            key=lambda item: compute_hierarchical_order(item["loop_question"])
        )

        for record in year_records:
            subq_map = record["subquestions"]
            if isinstance(subq_map, OrderedDict):
                orders = sorted(subq_map.keys())
                if orders != list(range(1, len(orders) + 1)):
                    raise ValueError(
                        f"Órdenes de subpreguntas no consecutivos en {record['loop_question']} ({year}): {orders}"
                    )
                record["subquestions"] = [
                    {"order": int(o), "text": subq_map[o]} for o in orders
                ]

        all_records.extend(year_records)
        logger.debug(
            f"Año {year}: {len(year_records)} preguntas de bucle identificadas estructuralmente."
        )

    return all_records


# -----------------------------------------------------------------------------
# LOOKUPS CENTRALIZADOS VÍA ORM
# -----------------------------------------------------------------------------


async def get_indicator_sections_map(
    conn: AsyncConnection, years: tuple[int, ...]
) -> dict[tuple[int, str, str, str], str]:
    """Relaciona de forma única el año + códigos normalizados de jerarquía con el ID de su INDICADOR."""
    stmt = (
        select(
            Form.code.label("form_year"),
            Section.label.label("indicator_label"),
            Section.id.label("indicator_id"),
            Section.parent_id.label("parent_var_id"),
        )
        .join(Form, Form.id == Section.form_id)
        .join(SectionType, SectionType.id == Section.section_type_id)
        .where(SectionType.label.like("%INDICADOR%"))
    )
    indicator_rows = (await conn.execute(stmt)).mappings().all()
    if not indicator_rows:
        return {}

    all_sections_stmt = select(Section.id, Section.label, Section.parent_id)
    all_sections = {
        str(r["id"]): {
            "label": r["label"],
            "parent_id": str(r["parent_id"]) if r["parent_id"] else None,
        }
        for r in (await conn.execute(all_sections_stmt)).mappings().all()
    }

    lookup: dict[tuple[int, str, str, str], str] = {}
    for row in indicator_rows:
        year = int(row["form_year"])
        if year not in years:
            continue

        var_id = row["parent_var_id"]
        if not var_id or str(var_id) not in all_sections:
            continue
        var_data = all_sections[str(var_id)]

        comp_id = var_data["parent_id"]
        if not comp_id or str(comp_id) not in all_sections:
            continue
        comp_data = all_sections[str(comp_id)]

        key = (
            year,
            fold_for_comparison(comp_data["label"]) or "",
            fold_for_comparison(var_data["label"]) or "",
            fold_for_comparison(row["indicator_label"]) or "",
        )
        lookup[key] = str(row["indicator_id"])

    return lookup


async def get_existing_questions(
    conn: AsyncConnection, years: tuple[int, ...]
) -> dict[tuple[int, str], dict]:
    """Mapea (año, label_normalizado) -> registro de la pregunta persistida en la BD."""
    stmt = (
        select(
            Question.id.label("question_id"),
            Question.section_id,
            Question.code,
            Question.label,
            Question.description,
            Question.display_order,
            Question.required,
            Question.is_loop,
            Form.code.label("form_year"),
        )
        .join(Section, Section.id == Question.section_id)
        .join(Form, Form.id == Section.form_id)
    )
    rows = (await conn.execute(stmt)).mappings().all()

    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in rows:
        y = int(row["form_year"])
        if y in years:
            natural_label = fold_for_comparison(row["label"]) or ""
            grouped[(y, natural_label)].append(dict(row))

    existing: dict[tuple[int, str], dict] = {}
    for key, items in grouped.items():
        if len(items) > 1:
            raise ValueError(
                f"Preguntas duplicadas detectadas para la clave natural {key}."
            )
        existing[key] = items[0]

    return existing


# -----------------------------------------------------------------------------
# EJECUCIÓN CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(FILE_PATH)
    years = get_seeding_active_years()

    if not path.is_file():
        raise FileNotFoundError(
            f"Archivo de estructura no localizado en la ruta: {path}"
        )

    logger.debug(
        f"Iniciando el poblado de preguntas tipo bucle para los años {years} desde {path}..."
    )

    excel = pd.ExcelFile(path)
    loops = load_loops_from_excel(excel, years)

    async with async_engine.begin() as conn:
        # Validación e introspección dinámica de las columnas físicas reales de la tabla
        db_columns = await get_table_columns(conn, schema="forms", table="questions")
        validate_required_columns(
            db_columns,
            required={
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
            },
            table_name="forms.questions",
        )

        indicators_map = await get_indicator_sections_map(conn, years)
        questions_map = await get_existing_questions(conn, years)
        helper_value = None if db_columns["helper"]["nullable"] else ""

        inserted = 0
        updated = 0
        mixed_updated = 0

        for loop in loops:
            year = loop["year"]
            hierarchy_key = (
                year,
                fold_for_comparison(loop["component"]) or "",
                fold_for_comparison(loop["variable"]) or "",
                fold_for_comparison(loop["indicator"]) or "",
            )
            section_id = indicators_map.get(hierarchy_key)
            if section_id is None:
                raise ValueError(
                    f"No se encontró INDICADOR para {loop['loop_question']} ({year}). Jerarquía: {hierarchy_key}"
                )

            parent_key = (year, fold_for_comparison(loop["parent_question"]) or "")
            parent = questions_map.get(parent_key)
            if parent is None:
                raise ValueError(
                    f"No existe la pregunta principal '{loop['parent_question']}' ({year}) requerida para el bucle. "
                    "Asegúrate de ejecutar el poblado de preguntas principales antes."
                )
            if str(parent["section_id"]) != str(section_id):
                raise ValueError(
                    f"La pregunta principal y su bucle '{loop['loop_question']}' ({year}) no coinciden en sección."
                )

            loop_key = (year, fold_for_comparison(loop["loop_question"]) or "")
            existing = questions_map.get(loop_key)

            # Caso de Negocio: Pregunta es principal y bucle de forma simultánea (Bucle Mixto)
            if loop["is_mixed"]:
                if existing is None or str(existing["question_id"]) != str(
                    parent["question_id"]
                ):
                    raise ValueError(
                        f"El bucle mixto {loop['loop_question']} ({year}) debe reutilizar la pregunta principal existente."
                    )

                stmt_mixed = (
                    update(Question)
                    .where(Question.id == parent["question_id"])
                    .values(
                        section_id=section_id,
                        helper=helper_value,
                        required=True,
                        is_loop=True,
                    )
                )
                await conn.execute(stmt_mixed)
                mixed_updated += 1
                continue

            # Caso Estándar: Pregunta Bucle independiente
            question_id = existing["question_id"] if existing else new_uuidv7()
            raw_num = re.sub(r"[^\d.]", "", loop["loop_question"]).replace(".", "_")
            code_identifier = (
                f"{year}_Q{raw_num}" if raw_num else f"{year}_{loop['loop_question']}"
            )

            db_payload = {
                "id": question_id,
                "code": code_identifier,
                "section_id": section_id,
                "file_id": None,
                "label": truncate_text(
                    loop["loop_question"], db_columns["label"]["max_length"]
                ),
                "description": truncate_text(
                    loop["loop_text"], db_columns["description"]["max_length"]
                ),
                "helper": helper_value,
                "display_order": int(compute_hierarchical_order(loop["loop_question"])),
                "required": True,
                "is_loop": True,
            }

            if existing:
                stmt_update = (
                    update(Question)
                    .where(Question.id == db_payload["id"])
                    .values(
                        code=db_payload["code"],
                        section_id=db_payload["section_id"],
                        file_id=db_payload["file_id"],
                        label=db_payload["label"],
                        description=db_payload["description"],
                        helper=db_payload["helper"],
                        display_order=db_payload["display_order"],
                        required=db_payload["required"],
                        is_loop=db_payload["is_loop"],
                    )
                )
                await conn.execute(stmt_update)
                updated += 1
            else:
                stmt_insert = insert(Question).values(db_payload)
                await conn.execute(stmt_insert)
                inserted += 1

            # Sincronizar en caliente el mapa local para evitar colisiones por dependencias internas
            questions_map[loop_key] = {
                "question_id": question_id,
                "section_id": section_id,
                "code": code_identifier,
                "label": loop["loop_question"],
                "description": loop["loop_text"],
                "display_order": db_payload["display_order"],
                "required": True,
                "is_loop": True,
            }

        # -----------------------------------------------------------------------------
        # ASERCIONES FINALES DE SANIDAD POST-CARGA CENTRALIZADA
        # -----------------------------------------------------------------------------
        stmt_validate = (
            select(Question.id, Question.code)
            .join(Section, Section.id == Question.section_id)
            .where(
                Section.form_id.in_(
                    select(Form.id).where(Form.code.in_([str(y) for y in years]))
                )
            )
        )
        final_rows = [
            dict(r) for r in (await conn.execute(stmt_validate)).mappings().all()
        ]

        assert_all_uuidv7(rows=final_rows, id_key="id", label_key="code")
        assert_no_duplicates(
            rows=final_rows,
            key_fields=["code"],
            what="preguntas tipo bucle e independientes de formularios",
        )

    logger.info(
        f"Poblado de preguntas bucle finalizado exitosamente. "
        f"Insertados: {inserted}. Actualizados: {updated}. Mixtos Actualizados: {mixed_updated}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
