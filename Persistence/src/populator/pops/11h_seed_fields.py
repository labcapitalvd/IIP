"""Puebla forms.fields para los IIP mapeando a través de la jerarquía FieldGroup.

Dependencias previas:
    - seed_questions (Preguntas principales cargadas)
    - seed_loop_questions (Preguntas tipo bucle cargadas)
    - seed_card_templates (Plantillas de tarjetas cargadas)
    - seed_field_groups (Grupos de campos repetibles cargadas)

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva los UUIDv7 existentes de forma transparente.
"""

import asyncio
import os
from collections import OrderedDict, defaultdict
from pathlib import Path

import pandas as pd

# Importación de Enums Globales del Sistema
from shared.enums import FieldTypesEnum

# Infraestructura y Registro global del proyecto
from shared.infrastructure import async_engine

# Importación de Modelos ORM Centralizados
from shared.models import (
    CardTemplate,
    Field,
    FieldGroup,
    FieldType,
    Form,
    Question,
    Section,
)
from shared.utils.logger import get_logger

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


def load_fields_for_years(excel: pd.ExcelFile, years: tuple[int, ...]) -> list[dict]:
    all_fields: list[dict] = []

    for year in years:
        sheet_name = str(year)
        if sheet_name not in excel.sheet_names:
            logger.debug(f"Hoja {sheet_name!r} no encontrada. Omitiendo.")
            continue

        temp_df = pd.read_excel(excel, sheet_name=sheet_name, nrows=1, dtype=object)
        temp_cols = {str(c).strip() for c in temp_df.columns}

        q_col = "Pregunta" if "Pregunta" in temp_cols else "COD_PREGUNTA"
        sub_col = "Subpregunta" if "Subpregunta" in temp_cols else "COD_SUBPREGUNTA"

        f_code_col = next(
            (c for c in ["Codigo_Campo", "COD_CAMPO", "Campo"] if c in temp_cols),
            "Campo",
        )
        f_lbl_col = next(
            (
                c
                for c in ["Nombre de la innovación", "Etiqueta", "DESCRIPCION_CAMPO"]
                if c in temp_cols
            ),
            f_code_col,
        )
        f_desc_col = next(
            (c for c in ["DESCRIPCION", "Enunciado"] if c in temp_cols), f_lbl_col
        )

        required_cols = {q_col}
        frame = load_clean_excel_sheet(
            excel, sheet_name=sheet_name, required_columns=required_cols
        )
        sheet_fields: OrderedDict[tuple[str, str], dict] = OrderedDict()

        display_order_counter = defaultdict(int)

        for idx, (_, row) in enumerate(frame.iterrows(), start=2):
            row_idx = idx
            parent_question = clean_text(row.get(q_col))
            subquestion = clean_text(row.get(sub_col))
            field_code = clean_text(row.get(f_code_col))
            field_label = clean_text(row.get(f_lbl_col)) or field_code
            field_description = clean_text(row.get(f_desc_col)) or field_label

            if parent_question is None or (field_code is None and subquestion is None):
                continue

            target_question_label = subquestion or parent_question
            code = field_code or f"FIELD_{row_idx}"

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
# LOOKUPS CENTRALIZADOS VÍA ORM
# -----------------------------------------------------------------------------


async def get_questions_lookup(
    conn: AsyncConnection, years: tuple[int, ...]
) -> dict[tuple[int, str], dict]:
    stmt = (
        select(
            Question.id.label("question_id"),
            Question.label,
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


async def get_field_groups_lookup(conn: AsyncConnection) -> dict[str, str]:
    stmt = select(FieldGroup.id.label("field_group_id"), CardTemplate.question_id).join(
        CardTemplate, FieldGroup.card_template_id == CardTemplate.id
    )
    rows = (await conn.execute(stmt)).mappings().all()
    return {str(row["question_id"]): str(row["field_group_id"]) for row in rows}


async def get_existing_fields(conn: AsyncConnection) -> dict[tuple[str, str], dict]:
    stmt = select(
        Field.id.label("field_id"),
        Field.field_group_id,
        Field.field_type_id,
        Field.code,
        Field.label,
        Field.description,
        Field.display_order,
        Field.required,
    )
    rows = (await conn.execute(stmt)).mappings().all()

    grouped = defaultdict(list)
    for row in rows:
        key = (str(row["field_group_id"]), fold_for_comparison(row["code"]) or "")
        grouped[key].append(dict(row))

    lookup = {}
    for key, items in grouped.items():
        if len(items) > 1:
            raise ValueError(
                f"Inconsistencia física: Campos duplicados bajo el mismo grupo y código: {key}."
            )
        lookup[key] = items[0]
    return lookup


# -----------------------------------------------------------------------------
# EJECUCIÓN CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(FILE_PATH)
    years = get_seeding_active_years()
    if not path.is_file():
        raise FileNotFoundError(f"Archivo de origen Excel no encontrado: {path}")

    logger.debug(f"Iniciando el poblado de forms.fields desde {path}...")

    excel = pd.ExcelFile(path)
    raw_fields = load_fields_for_years(excel, years)

    async with async_engine.begin() as conn:
        # Validación e introspección dinámica de las columnas físicas reales de la tabla
        db_columns = await get_table_columns(conn, schema="forms", table="fields")
        validate_required_columns(
            db_columns,
            required={
                "id",
                "field_group_id",
                "field_type_id",
                "code",
                "label",
                "description",
                "required",
                "display_order",
            },
            table_name="forms.fields",
        )

        has_field_group_col = "field_group_id" in db_columns

        # USO DEL ENUM: Consulta limpia utilizando la propiedad explícita .code ("text")
        stmt_type = select(FieldType.id).where(
            FieldType.code == FieldTypesEnum.TEXT.code
        )
        type_row = (await conn.execute(stmt_type)).mappings().first()

        if not type_row:
            raise ValueError(
                f"Catálogo maestro incompleto: No se encontró el registro para el tipo de campo "
                f"'{FieldTypesEnum.TEXT.code}' en la tabla de tipos correspondientes."
            )
        default_field_type_id = str(type_row["id"])

        # Inicialización de matrices de búsqueda compartidas relacionales
        questions_map = await get_questions_lookup(conn, years)
        field_groups_map = await get_field_groups_lookup(conn)
        existing_fields = await get_existing_fields(conn)

        expected_records = []
        for item in raw_fields:
            y = item["year"]
            lbl_key = fold_for_comparison(item["target_question_label"]) or ""

            question = questions_map.get((y, lbl_key))
            if question is None:
                raise ValueError(
                    f"Fallo relacional: No se localizó la pregunta '{item['target_question_label']}' ({y}) en forms.questions."
                )

            q_id_str = str(question["question_id"])
            fg_id_str = field_groups_map.get(q_id_str)

            if fg_id_str is None:
                logger.warning(
                    f"Pregunta '{item['target_question_label']}' ({y}) no tiene un grupo de campos asignado. "
                    f"Asegúrate de haber corrido seed_field_groups.py para este año. Omitiendo campo."
                )
                continue

            expected_records.append(
                {
                    "natural_key": (fg_id_str, fold_for_comparison(item["code"]) or ""),
                    "field_group_id": fg_id_str,
                    "field_type_id": default_field_type_id,
                    "code": item["code"],
                    "label": item["label"],
                    "description": item["description"],
                    "display_order": item["display_order"],
                }
            )

        inserted, updated = 0, 0

        for source in expected_records:
            old_field = existing_fields.get(source["natural_key"])
            field_id = old_field["field_id"] if old_field else new_uuidv7()

            db_payload = {
                "id": field_id,
                "field_group_id": source["field_group_id"],
                "field_type_id": source["field_type_id"],
                "code": truncate_text(source["code"], db_columns["code"]["max_length"]),
                "label": truncate_text(
                    source["label"], db_columns["label"]["max_length"]
                ),
                "description": truncate_text(
                    source["description"], db_columns["description"]["max_length"]
                ),
                "required": True,
                "display_order": source["display_order"],
            }

            if old_field:
                stmt_update = (
                    update(Field)
                    .where(Field.id == db_payload["id"])
                    .values(
                        field_group_id=db_payload["field_group_id"],
                        field_type_id=db_payload["field_type_id"],
                        code=db_payload["code"],
                        label=db_payload["label"],
                        description=db_payload["description"],
                        required=db_payload["required"],
                        display_order=db_payload["display_order"],
                    )
                )
                await conn.execute(stmt_update)
                updated += 1
            else:
                stmt_insert = insert(Field).values(db_payload)
                await conn.execute(stmt_insert)
                inserted += 1

        # -----------------------------------------------------------------------------
        # ASERCIONES FINALES DE SANIDAD POST-CARGA CENTRALIZADA
        # -----------------------------------------------------------------------------
        final_stmt = select(Field.id, Field.code)
        final_rows = [
            dict(r) for r in (await conn.execute(final_stmt)).mappings().all()
        ]

        assert_all_uuidv7(rows=final_rows, id_key="id", label_key="code")
        assert_no_duplicates(
            rows=final_rows,
            key_fields=["code"],
            what="campos de entrada de preguntas (fields)",
        )

    logger.info(
        f"Poblado de forms.fields finalizado exitosamente. "
        f"Insertados: {inserted}. Actualizados: {updated}. Totales Esperados: {len(expected_records)}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
