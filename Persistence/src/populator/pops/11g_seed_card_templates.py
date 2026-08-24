"""Puebla forms.card_templates para los bucles de los formularios IIP.

Dependencias previas:
    - seed_questions (Preguntas principales cargadas)
    - seed_loop_questions (Preguntas tipo bucle cargadas)

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva los UUIDv7 existentes de forma transparente.
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
from shared.models import CardTemplate, Form, Question, Section
from shared.utils.logger import getLogger

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

logger = getLogger(__name__)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN ESPECÍFICA DE ÁMBITO
# -----------------------------------------------------------------------------

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

# -----------------------------------------------------------------------------
# IDENTIFICADORES TÉCNICOS Y TRATAMIENTO LOCAL
# -----------------------------------------------------------------------------


def make_template_code_local(year: int, loop_question_label: str) -> str:
    """Genera un código técnico limpio y consistente para la plantilla.

    Ejemplos:
        Pregunta 1.1 -> 2023_CT_Q1_1
        Pregunta 28.1 -> 2023_CT_Q28_1
    """
    suffix = extract_numeric_suffix(loop_question_label)
    if suffix:
        return f"{year}_CT_Q{suffix}"

    folded = fold_for_comparison(loop_question_label) or "sin_codigo"
    cleaned = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
    return f"{year}_CT_{cleaned}"


# -----------------------------------------------------------------------------
# ETL Y EXTRACCION DESDE EL LIBRO EXCEL
# -----------------------------------------------------------------------------


def load_loops_from_excel(excel: pd.ExcelFile, year: int) -> list[dict]:
    sheet_name = str(year)
    if sheet_name not in excel.sheet_names:
        logger.warning(f"Hoja para el año {year} no encontrada en el Excel. Omitiendo.")
        return []

    # Remojamos la validación estricta de la columna "Bucle" para permitir hojas tradicionales (2019/2021)
    required_cols = {"Pregunta"}
    frame = load_clean_excel_sheet(
        excel, sheet_name=sheet_name, required_columns=required_cols
    )

    registry: OrderedDict[str, dict] = OrderedDict()

    for idx, (_, row) in enumerate(frame.iterrows(), start=2):
        row_idx = idx

        parent_question = clean_text(row["Pregunta"])
        if parent_question is None:
            continue  # Ignorar filas completamente rotas o vacías

        # Fallback adaptativo: Si no es un bucle, la tarjeta apunta a la pregunta principal
        loop_question = clean_text(row.get("Bucle")) or parent_question

        # Extraer etiquetas con fallback seguro
        card_template_label = (
            clean_text(row.get("card_template"))
            if "card_template" in frame.columns
            else None
        ) or loop_question

        # Extraer descripciones con fallback seguro
        card_template_desc = (
            clean_text(row.get("desc_card_template"))
            if "desc_card_template" in frame.columns
            else None
        ) or loop_question

        candidate = {
            "year": year,
            "loop_question": loop_question,
            "loop_label": card_template_label,
            "loop_text": card_template_desc,
            "parent_question": parent_question,
            "is_mixed": loop_question == parent_question,
        }

        existing = registry.get(loop_question)
        if existing is None:
            registry[loop_question] = candidate
            continue

        if fold_for_comparison(existing["loop_text"]) != fold_for_comparison(
            card_template_desc
        ):
            raise ValueError(
                f"Informacion contradictoria detectada para el bucle '{loop_question}' en el año {year}."
            )

    return list(registry.values())


# -----------------------------------------------------------------------------
# LOOKUPS CENTRALIZADOS VÍA ORM
# -----------------------------------------------------------------------------


async def get_form_by_year(conn: AsyncConnection, year: int) -> str | None:
    stmt = select(Form.id).where(Form.code == str(year))
    row = (await conn.execute(stmt)).mappings().first()
    return str(row["id"]) if row else None


async def get_questions_lookup(conn: AsyncConnection, form_id: str) -> dict[str, dict]:
    stmt = (
        select(
            Question.id.label("question_id"),
            Question.label,
            Question.description,
            Question.is_loop,
        )
        .join(Section, Section.id == Question.section_id)
        .where(Section.form_id == form_id)
    )
    result = await conn.execute(stmt)

    grouped = defaultdict(list)
    for row in result.mappings().all():
        natural_label = fold_for_comparison(row["label"]) or ""
        grouped[natural_label].append(dict(row))

    lookup = {}
    for key, items in grouped.items():
        if len(items) > 1:
            raise ValueError(
                f"Inconsistencia: Preguntas duplicadas para el label '{key}' dentro del formulario."
            )
        lookup[key] = items[0]
    return lookup


async def get_existing_templates(conn: AsyncConnection) -> dict[str, dict]:
    """Mapea el id de la pregunta con su único card_template registrado."""
    stmt = select(
        CardTemplate.id.label("card_template_id"),
        CardTemplate.question_id,
        CardTemplate.code,
        CardTemplate.label,
        CardTemplate.description,
        CardTemplate.helper,
    )
    result = await conn.execute(stmt)

    grouped = defaultdict(list)
    for row in result.mappings().all():
        grouped[str(row["question_id"])].append(dict(row))

    lookup = {}
    for question_id, items in grouped.items():
        if len(items) > 1:
            raise ValueError(
                f"La pregunta '{question_id}' cuenta con múltiples plantillas card_templates."
            )
        lookup[question_id] = items[0]
    return lookup


# -----------------------------------------------------------------------------
# EJECUCIÓN CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(FILE_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"Archivo de origen Excel no encontrado: {path}")

    active_years = get_seeding_active_years()
    logger.debug(
        f"Iniciando el poblado de forms.card_templates desde {path} para los años: {active_years}"
    )

    excel = pd.ExcelFile(path)

    async with async_engine.begin() as conn:
        # Validación e introspección dinámica de las columnas físicas reales de la tabla
        db_columns = await get_table_columns(
            conn, schema="forms", table="card_templates"
        )
        validate_required_columns(
            db_columns,
            required={"id", "question_id", "code", "label", "description", "helper"},
            table_name="forms.card_templates",
        )

        helper_value = None if db_columns["helper"]["nullable"] else ""
        existing_templates = await get_existing_templates(conn)

        total_inserted = 0
        total_updated = 0

        for year in active_years:
            loops = load_loops_from_excel(excel, year)
            if not loops:
                continue

            form_id = await get_form_by_year(conn, year)
            if not form_id:
                logger.warning(
                    f"No existe el formulario operacional registrado para el año {year}. Omitiendo."
                )
                continue

            questions_map = await get_questions_lookup(conn, form_id)

            inserted = 0
            updated = 0

            for source in loops:
                natural_loop_lbl = fold_for_comparison(source["loop_question"]) or ""
                question = questions_map.get(natural_loop_lbl)

                if question is None:
                    raise ValueError(
                        f"Fallo relacional: No se localizó la pregunta '{source['loop_question']}' en forms.questions "
                        f"para el año {year}. Asegúrate de ejecutar seed_loop_questions.py previamente."
                    )
                # if question["is_loop"] is not True:
                #     raise ValueError(
                #         f"La pregunta '{source['loop_question']}' (Año {year}) no está configurada como is_loop = TRUE."
                #     )

                q_id_str = str(question["question_id"])
                old_template = existing_templates.get(q_id_str)

                # Mantener la idempotencia preservando identificadores UUIDv7 previos
                card_template_id = (
                    old_template["card_template_id"] if old_template else new_uuidv7()
                )
                template_code = make_template_code_local(year, source["loop_question"])

                db_payload = {
                    "id": card_template_id,
                    "question_id": q_id_str,
                    "code": truncate_text(
                        template_code, db_columns["code"]["max_length"]
                    ),
                    "label": truncate_text(
                        source["loop_label"], db_columns["label"]["max_length"]
                    ),
                    "description": truncate_text(
                        source["loop_text"], db_columns["description"]["max_length"]
                    ),
                    "helper": helper_value,
                }

                if old_template:
                    stmt_update = (
                        update(CardTemplate)
                        .where(CardTemplate.id == db_payload["id"])
                        .values(
                            question_id=db_payload["question_id"],
                            code=db_payload["code"],
                            label=db_payload["label"],
                            description=db_payload["description"],
                            helper=db_payload["helper"],
                        )
                    )
                    await conn.execute(stmt_update)
                    updated += 1
                else:
                    stmt_insert = insert(CardTemplate).values(db_payload)
                    await conn.execute(stmt_insert)
                    inserted += 1

            total_inserted += inserted
            total_updated += updated

        # -----------------------------------------------------------------------------
        # ASERCIONES FINALES DE SANIDAD POST-CARGA CENTRALIZADA
        # -----------------------------------------------------------------------------
        final_stmt = select(CardTemplate.id, CardTemplate.code)
        final_rows = [
            dict(r) for r in (await conn.execute(final_stmt)).mappings().all()
        ]

        assert_all_uuidv7(rows=final_rows, id_key="id", label_key="code")
        assert_no_duplicates(
            rows=final_rows,
            key_fields=["code"],
            what="plantillas de tarjetas (card_templates)",
        )

    logger.info(
        f"Poblado de forms.card_templates finalizado exitosamente. "
        f"Total Creados: {total_inserted}. Total Actualizados: {total_updated}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
