"""Puebla forms.field_groups para los IIP.

Dependencias previas:
    - seed_questions (Preguntas principales cargadas)
    - seed_loop_questions (Preguntas tipo bucle cargadas)
    - seed_card_templates (Plantillas de tarjetas cargadas)

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva los UUIDv7 existentes de forma transparente.
"""

import asyncio
import os
from collections import OrderedDict, defaultdict
from pathlib import Path

import pandas as pd

# Infraestructura y Registro global del proyecto
from shared.infrastructure import async_engine

# Importación de Modelos ORM Centralizados desde tu Módulo init
from shared.models import CardTemplate, FieldGroup, Form, Question, Section
from shared.utils.logger import getLogger

# Utilidades Core de Seeding Compartidas (Elimina duplicación)
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_no_duplicates,
    clean_text,
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
# ETL Y EXTRACCIÓN DESDE EL LIBRO EXCEL
# -----------------------------------------------------------------------------


def load_loops_for_years(excel: pd.ExcelFile, years: tuple[int, ...]) -> list[dict]:
    all_loops: list[dict] = []

    for year in years:
        sheet_name = str(year)
        if sheet_name not in excel.sheet_names:
            logger.debug(f"Hoja {sheet_name!r} no encontrada. Omitiendo.")
            continue

        # Lectura previa parcial para evaluar la existencia de columnas condicionales de bucle
        temp_df = pd.read_excel(excel, sheet_name=sheet_name, nrows=1, dtype=object)
        temp_cols = [str(c).strip() for c in temp_df.columns]
        if "Bucle" not in temp_cols:
            logger.debug(f"Hoja {sheet_name!r} no contiene columna 'Bucle'. Omitiendo.")
            continue

        bucle_col = "card_template" if "card_template" in temp_cols else "card_template"
        required_cols = {"Pregunta", "Bucle", bucle_col}

        frame = load_clean_excel_sheet(
            excel, sheet_name=sheet_name, required_columns=required_cols
        )
        sheet_loops: OrderedDict[str, dict] = OrderedDict()

        # Enumerate garantiza que row_idx sea tratado como int estricto para los validadores estáticos

        for idx, (_, row) in enumerate(frame.iterrows(), start=2):
            row_idx = idx

            parent_question = clean_text(row.get("Pregunta"))
            if parent_question is None:
                continue

            # Fallback to parent text if Bucle is absent (standard linear item)
            loop_question = clean_text(row.get("Bucle")) or parent_question
            loop_text = clean_text(row.get(bucle_col)) or loop_question

            excel_code = clean_text(row.get("code_field_groups")) or "MAIN"
            excel_label = clean_text(row.get("field_group")) or loop_text
            excel_description = clean_text(row.get("desc_field_group")) or excel_label

            # Format uniform database technical identification keys
            q_clean = (
                str(loop_question)
                .replace("Pregunta", "Q")
                .replace(".", "_")
                .replace(" ", "")
            )
            code_fg = f"{year}_FG_{q_clean}_{excel_code}".strip("_")

            candidate = {
                "year": year,
                "loop_question": loop_question,
                "loop_text": loop_text,
                "parent_question": parent_question,
                "is_mixed": loop_question == parent_question,
                "code": code_fg,
                "label": excel_label,
                "description": excel_description,
            }

            # Deduplicate by group code to allow consecutive variable lines to bind cleanly
            old = sheet_loops.get(code_fg)
            if old is None:
                sheet_loops[code_fg] = candidate
            elif fold_for_comparison(old["loop_text"]) != fold_for_comparison(
                loop_text
            ):
                raise ValueError(
                    f"Información contradictoria para el grupo {code_fg} en la hoja {year}."
                )

        all_loops.extend(sheet_loops.values())

    return all_loops


# -----------------------------------------------------------------------------
# LOOKUPS CENTRALIZADOS VÍA ORM
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
                f"Debe existir un único formulario para el año {year} en forms.forms."
            )
        lookup[year] = ids[0]
    return lookup


async def get_questions_lookup(
    conn: AsyncConnection, years: tuple[int, ...]
) -> dict[tuple[int, str], dict]:
    stmt = (
        select(
            Question.id.label("question_id"),
            Question.label,
            Question.is_loop,
            Form.code.label("form_year"),
        )
        .join(Section, Section.id == Question.section_id)
        .join(Form, Form.id == Section.form_id)
    )
    rows = (await conn.execute(stmt)).mappings().all()

    grouped = defaultdict(list)
    for row in rows:
        y = int(row["form_year"])
        if y in years:
            natural_lbl = fold_for_comparison(row["label"]) or ""
            grouped[(y, natural_lbl)].append(dict(row))

    lookup = {}
    for key, items in grouped.items():
        if len(items) > 1:
            raise ValueError(
                f"Inconsistencia: Preguntas duplicadas detectadas para la clave natural {key}."
            )
        lookup[key] = items[0]
    return lookup


async def get_card_templates_lookup(conn: AsyncConnection) -> dict[str, dict]:
    stmt = select(
        CardTemplate.id.label("card_template_id"),
        CardTemplate.question_id,
        CardTemplate.code,
    )
    rows = (await conn.execute(stmt)).mappings().all()

    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row["question_id"])].append(dict(row))

    lookup = {}
    for q_id, items in grouped.items():
        if len(items) > 1:
            raise ValueError(
                f"La pregunta '{q_id}' cuenta con múltiples plantillas card_templates vinculadas."
            )
        lookup[q_id] = items[0]
    return lookup


async def get_existing_groups(
    conn: AsyncConnection,
) -> dict[tuple[str, str, str], dict]:
    """Mapea la tupla indexada (question_id, card_template_id, code) con su registro persistido."""
    stmt = (
        select(
            FieldGroup.id.label("field_group_id"),
            Section.form_id,
            CardTemplate.question_id,
            FieldGroup.card_template_id,
            FieldGroup.code,
            FieldGroup.label,
            FieldGroup.description,
            FieldGroup.display_order,
        )
        .join(CardTemplate, FieldGroup.card_template_id == CardTemplate.id)
        .join(Question, CardTemplate.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
    )
    rows = (await conn.execute(stmt)).mappings().all()

    # SOLUCIÓN: Agrupar usando la clave compuesta de 3 elementos para permitir re-runs idempotentes
    lookup = {}
    for row in rows:
        key = (
            str(row["question_id"]),
            str(row["card_template_id"]),
            str(row["code"]).strip(),
        )
        if key in lookup:
            raise ValueError(
                f"Error crítico: El código de grupo '{row['code']}' ya existe para esta plantilla de tarjeta."
            )
        lookup[key] = dict(row)

    return lookup


# -----------------------------------------------------------------------------
# EJECUCION CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(FILE_PATH)
    years = get_seeding_active_years()
    if not path.is_file():
        raise FileNotFoundError(f"Archivo de origen Excel no encontrado: {path}")

    logger.debug(f"Iniciando el poblado de forms.field_groups desde {path}...")

    excel = pd.ExcelFile(path)
    loops = load_loops_for_years(excel, years)

    async with async_engine.begin() as conn:
        db_columns = await get_table_columns(conn, schema="forms", table="field_groups")
        validate_required_columns(
            db_columns,
            required={
                "id",
                "card_template_id",
                "code",
                "label",
                "description",
                "display_order",
            },
            table_name="forms.field_groups",
        )

        forms_map = await get_forms_lookup(conn, years)
        questions_map = await get_questions_lookup(conn, years)
        templates_map = await get_card_templates_lookup(conn)
        existing_groups = await get_existing_groups(conn)

        expected_records = []
        for loop in loops:
            y = loop["year"]
            lbl_key = fold_for_comparison(loop["loop_question"]) or ""

            question = questions_map.get((y, lbl_key))
            if question is None:
                raise ValueError(
                    f"Fallo relacional: No se localizo la pregunta '{loop['loop_question']}' ({y}) en forms.questions."
                )
            # if question["is_loop"] is not True:
            #     raise ValueError(
            #         f"La pregunta '{loop['loop_question']}' ({y}) tiene is_loop configurado como FALSE en BD."
            #     )

            q_id_str = str(question["question_id"])
            template = templates_map.get(q_id_str)
            if template is None:
                raise ValueError(
                    f"Fallo de dependencias: No se hallo un card_template para la pregunta ID '{q_id_str}' ({loop['loop_question']})."
                )

            db_group_code = loop["code"]
            expected_records.append(
                {
                    "natural_key": (
                        q_id_str,
                        str(template["card_template_id"]),
                        str(db_group_code).strip(),
                    ),
                    "form_id": forms_map[y],
                    "card_template_id": str(template["card_template_id"]),
                    "code": db_group_code,
                    "label": loop["label"],
                    "description": loop["description"],
                    "display_order": 2 if loop["is_mixed"] else 1,
                }
            )

        inserted, updated = 0, 0

        for source in expected_records:
            old_group = existing_groups.get(source["natural_key"])
            field_group_id = old_group["field_group_id"] if old_group else new_uuidv7()

            db_payload = {
                "id": field_group_id,
                "card_template_id": source["card_template_id"],
                "code": truncate_text(source["code"], db_columns["code"]["max_length"]),
                "label": truncate_text(
                    source["label"], db_columns["label"]["max_length"]
                ),
                "description": truncate_text(
                    source["description"], db_columns["description"]["max_length"]
                ),
                "display_order": source["display_order"],
            }

            if old_group:
                stmt_update = (
                    update(FieldGroup)
                    .where(FieldGroup.id == db_payload["id"])
                    .values(
                        card_template_id=db_payload["card_template_id"],
                        code=db_payload["code"],
                        label=db_payload["label"],
                        description=db_payload["description"],
                        display_order=db_payload["display_order"],
                    )
                )
                await conn.execute(stmt_update)
                updated += 1
            else:
                stmt_insert = insert(FieldGroup).values(db_payload)
                await conn.execute(stmt_insert)
                inserted += 1

        # -----------------------------------------------------------------------------
        # ASERCIONES FINALES DE SANIDAD POST-CARGA CENTRALIZADA
        # -----------------------------------------------------------------------------
        final_stmt = select(FieldGroup.id, FieldGroup.code)
        final_rows = [
            dict(r) for r in (await conn.execute(final_stmt)).mappings().all()
        ]

        assert_all_uuidv7(rows=final_rows, id_key="id", label_key="code")
        assert_no_duplicates(
            rows=final_rows,
            key_fields=["code"],
            what="grupos de campos repetibles (field_groups)",
        )

    logger.info(
        f"Poblado de forms.field_groups finalizado exitosamente. "
        f"Insertados: {inserted}. Actualizados: {updated}. Totales Procesados: {len(expected_records)}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
