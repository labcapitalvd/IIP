"""Puebla las preguntas principales del IIP en forms.questions.

Fuente:
    Estructura_IIP.xlsx

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva UUIDv7 existentes basándose en estrategias
de coincidencia por combinaciones únicas de años, etiquetas y jerarquías.
"""

import asyncio
import os
import re
from collections import OrderedDict, defaultdict
from pathlib import Path

import pandas as pd

# Infraestructura y Registro global del proyecto
from shared.infrastructure import async_engine

# Importación de Modelos ORM Centralizados desde tu Módulo init
from shared.models import Form, Question, Section, SectionType
from shared.utils.logger import get_logger

# Utilidades Core de Seeding Compartidas (Elimina duplicación)
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_no_duplicates,
    clean_text,
    compute_hierarchical_order,
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

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)


# -----------------------------------------------------------------------------
# ETL Y EXTRACCIÓN DESDE EL LIBRO EXCEL
# -----------------------------------------------------------------------------


def load_questions_from_excel(
    excel: pd.ExcelFile, years: tuple[int, ...]
) -> list[dict]:
    """Construye preguntas principales únicas y su jerarquía metodológica."""
    records: list[dict] = []

    for year in years:
        required_cols = {
            "Componente",
            "Variable",
            "Indicador",
            "Pregunta",
            "pre",
        }

        # Cargar la hoja limpia usando la utilidad core centralizada
        frame = load_clean_excel_sheet(
            excel, sheet_name=str(year), required_columns=required_cols
        )

        has_loop_columns = "Bucle" in frame.columns and f"Bucle {year}" in frame.columns

        data = pd.DataFrame(
            {
                "source_row": frame.index + 2,
                "component": frame["Componente"],
                "variable": frame["Variable"],
                "indicator": frame["Indicador"],
                "question": frame["Pregunta"],
                "question_text": frame["pre"],
                "loop": frame["Bucle"] if has_loop_columns else None,
            }
        )

        for col in data.columns:
            if col != "source_row":
                data[col] = data[col].apply(clean_text)

        # Rellenar jerarquías combinadas
        hierarchy = ["component", "variable", "indicator"]
        data[hierarchy] = data[hierarchy].ffill()

        # Filtrar registros que cuenten con la estructura mínima requerida
        data = data[
            data[["component", "variable", "indicator", "question", "question_text"]]
            .notna()
            .all(axis=1)
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
                "is_loop": clean_text(row["loop"]) == question,
                "display_order": compute_hierarchical_order(question),
            }

            existing = registry.get(question)
            if existing is None:
                registry[question] = candidate
                continue

            # Validar que no existan contradicciones de negocio en filas duplicadas del Excel
            fields_to_check = ("component", "variable", "indicator", "question_text")
            conflicts = [
                f
                for f in fields_to_check
                if fold_for_comparison(existing[f]) != fold_for_comparison(candidate[f])
            ]
            if conflicts:
                raise ValueError(
                    f"Información contradictoria para {question} en la hoja {year}. "
                    f"Campos en conflicto: {conflicts}. Filas: {existing['source_row']} y {candidate['source_row']}."
                )

            existing["is_loop"] = existing["is_loop"] or candidate["is_loop"]

        year_records = list(registry.values())
        if not year_records:
            raise ValueError(
                f"La hoja {year} no produjo ninguna estructura de preguntas válida."
            )

        records.extend(year_records)
        logger.debug(
            f"Año {year}: {len(year_records)} preguntas principales procesadas."
        )

    return records


# -----------------------------------------------------------------------------
# ESTRUCTURAS DE LOOKUPS ACCEDIDAS VÍA ORM
# -----------------------------------------------------------------------------


async def get_forms_lookup(
    conn: AsyncConnection, years: tuple[int, ...]
) -> dict[int, str]:
    stmt = select(Form.code, Form.id).order_by(Form.code)
    rows = (await conn.execute(stmt)).mappings().all()

    grouped = defaultdict(list)
    for row in rows:
        y = int(row["code"])
        if y in years:
            grouped[y].append(str(row["id"]))

    lookup = {}
    for year in years:
        ids = grouped.get(year, [])
        if len(ids) != 1:
            raise ValueError(
                f"Debe existir un único formulario asignado para el año {year} en forms.forms."
            )
        lookup[year] = ids[0]

    return lookup


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

    # Extraer todas las secciones para reconstruir el árbol parental componente -> variable de manera eficiente
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

        # Added fallback strings to prevent str | None from being assigned into a strict str slot
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
    """Recupera el mapa de preguntas persistidas indexadas por el año del formulario y su etiqueta."""
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
        .join(
            Form, Form.id == Section.form_id
        )  # Fixed lowercase 'section' to uppercase 'Section'
    )
    rows = (await conn.execute(stmt)).mappings().all()

    # Explicit type annotation for the dictionary coordinates to satisfy the strict signature
    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in rows:
        y = int(row["form_year"])
        if y in years:
            # Applied fallback fallback string 'or ""' to satisfy strict 'str' tuple type engine constraints
            natural_label = fold_for_comparison(row["label"]) or ""
            grouped[(y, natural_label)].append(dict(row))

    existing: dict[tuple[int, str], dict] = {}
    for key, items in grouped.items():
        if len(items) > 1:
            raise ValueError(
                f"Inconsistencia de negocio: Existen preguntas duplicadas para la clave natural {key}."
            )
        existing[key] = items[0]

    return existing


# -----------------------------------------------------------------------------
# EJECUCIÓN CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(FILE_PATH)
    years = get_seeding_active_years()

    logger.debug(f"Iniciando el poblado de forms.questions desde {path}...")
    if not path.is_file():
        raise FileNotFoundError(
            f"Archivo de estructura no localizado en la ruta: {path}"
        )

    try:
        excel = pd.ExcelFile(path)
        source_records = load_questions_from_excel(excel, years)

        async with async_engine.begin() as conn:
            # Validación e introspección dinámica de las columnas físicas reales de la tabla
            db_columns = await get_table_columns(
                conn, schema="forms", table="questions"
            )
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

            # Inicialización de matrices de búsqueda compartidas
            forms_lookup = await get_forms_lookup(conn, years)
            indicators_map = await get_indicator_sections_map(conn, years)
            existing_questions = await get_existing_questions(conn, years)

            inserted, updated = 0, 0

            for source in source_records:
                hierarchy_key = (
                    source["year"],
                    fold_for_comparison(source["component"]),
                    fold_for_comparison(source["variable"]),
                    fold_for_comparison(source["indicator"]),
                )
                section_id = indicators_map.get(hierarchy_key)
                if section_id is None:
                    raise ValueError(
                        f"Fallo relacional: No se localizó la sección INDICADOR correspondiente para el año {source['year']} "
                        f"y la pregunta '{source['question']}'. Estructura buscada: {hierarchy_key}"
                    )

                natural_key = (source["year"], fold_for_comparison(source["question"]))
                old_record = existing_questions.get(natural_key)

                # Idempotencia: Preservar el identificador primario exacto en caso de existencia previa
                question_id = old_record["question_id"] if old_record else new_uuidv7()
                helper_value = None if db_columns["helper"]["nullable"] else ""

                # Normalización del código técnico de negocio para matching e indexación uniforme
                raw_num = re.sub(r"[^\d.]", "", source["question"]).replace(".", "_")
                code_identifier = (
                    f"{source['year']}_Q{raw_num}"
                    if raw_num
                    else f"{source['year']}_{source['question']}"
                )

                db_payload = {
                    "id": question_id,
                    "code": code_identifier,
                    "section_id": section_id,
                    "file_id": None,
                    "label": truncate_text(
                        source["question"], db_columns["label"]["max_length"]
                    ),
                    "description": truncate_text(
                        source["question_text"], db_columns["description"]["max_length"]
                    ),
                    "helper": helper_value,
                    "display_order": int(source["display_order"]),
                    "required": True,
                    "is_loop": bool(source["is_loop"]),
                }

                if old_record:
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

            # -----------------------------------------------------------------------------
            # ASERCIONES FINALES DE SANIDAD POST-CARGA CENTRALIZADA
            # -----------------------------------------------------------------------------
            final_stmt = (
                select(Question.id, Question.code)
                .join(Section, Section.id == Question.section_id)
                .where(Section.form_id.in_(list(forms_lookup.values())))
            )
            final_rows = [
                dict(r) for r in (await conn.execute(final_stmt)).mappings().all()
            ]

            assert_all_uuidv7(rows=final_rows, id_key="id", label_key="code")
            assert_no_duplicates(
                rows=final_rows,
                key_fields=["code"],
                what="preguntas principales de formularios",
            )

        logger.info(
            f"Poblado de forms.questions completado con éxito. Insertados: {inserted}. Actualizados: {updated}."
        )

    except Exception as exc:
        logger.error(f"Error crítico en el proceso de poblado de questions: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(upgrade())
