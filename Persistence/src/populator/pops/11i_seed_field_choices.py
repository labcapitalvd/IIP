"""Puebla forms.field_choices para los IIP mapeando opciones de selección.

Dependencia previa:
    - 11h_seed_fields (Campos de entrada creados y estructurados)

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva los UUIDv7 existentes de forma transparente.
"""

import asyncio
import os
import re
from pathlib import Path

import pandas as pd
from shared.enums import FieldTypesEnum
from shared.infrastructure import async_engine
from shared.models import (
    CardTemplate,
    Field,
    FieldChoice,
    FieldGroup,
    Form,
    Question,
    Section,
)
from shared.utils.logger import getLogger
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_no_duplicates,
    clean_text,
    fold_for_comparison,
    get_seeding_active_years,
    get_table_columns,
    new_uuidv7,
    truncate_text,
    validate_required_columns,
)
from sqlalchemy import insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncConnection

logger = get_getLogger = getLogger(__name__)

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

CHOICE_FIELD_TYPES = {
    FieldTypesEnum.SINGLE_CHOICE.code,
    FieldTypesEnum.MULTI_CHOICE.code,
}


def split_option_text(value: str, order: int) -> tuple[str, str]:
    cleaned = clean_text(value)
    if cleaned is None:
        return str(order), ""
    match = re.match(r"^\s*([A-Za-z]|\d+(?:[.,]\d+)*)\s*[\.)]\s*(.*)$", cleaned)
    if match:
        code = match.group(1).replace(",", ".").upper()
        description = clean_text(match.group(2))
        if description:
            return code, description
    return str(order), cleaned


def extract_clean_question_number(text_value: str) -> str:
    """Extracts a normalized, standardized key representing only the digits.
    Example: 'Pregunta 14.1'                        -> '14_1'
             'Pregunta 14'                          -> '14'
             '¿Existen dentro de la Pregunta 2...?' -> '2'
    """
    if not text_value:
        return ""
    # Search for an isolated number token in the string context
    match = re.search(
        r"(?:Pregunta\s+)?(\d+(?:[\._\.]\d+)*)", text_value, re.IGNORECASE
    )
    if match:
        return match.group(1).replace(".", "_")
    return ""


def load_choices_from_excel(excel: pd.ExcelFile, years: tuple[int, ...]) -> list[dict]:
    extracted_choices: list[dict] = []

    for year in years:
        if year == 2019:
            sheet_name = "2019"
        else:
            sheet_name = f"Respuestas_{year}"

        if sheet_name not in excel.sheet_names:
            continue

        df_raw = pd.read_excel(excel, sheet_name=sheet_name, header=None, dtype=object)

        is_reading_choices = True if year != 2019 else False
        col_map = {}

        for idx, row in df_raw.iterrows():
            if len(row) < 2:
                continue

            # Complete rewrite of the 2019 transition scanning tier
            if year == 2019 and not is_reading_choices:
                row_str_values = [
                    fold_for_comparison(cell) or "" for _, cell in row.items()
                ]
                if "pregunta" in row_str_values and "texto_pregunta" in row_str_values:
                    is_reading_choices = True
                    # Dynamically save index points by mapping text names cleanly
                    col_map = {
                        str(cell).strip(): i
                        for i, cell in enumerate(row.items())
                        if clean_text(cell)
                    }
                continue

            if not is_reading_choices:
                continue

            if year != 2019 and idx == 0:
                row_headers = [clean_text(cell) for _, cell in row.items()]
                col_map = {h: i for i, h in enumerate(row_headers) if h}
                continue

            q_key = "Pregunta"
            if q_key not in col_map:
                continue

            target_question_label = clean_text(row.iloc[col_map[q_key]])
            if target_question_label is None or target_question_label == q_key:
                continue

            type_key = "Tipo_pregunta" if "Tipo_pregunta" in col_map else "Tipo_dato"
            raw_field_type = clean_text(row.iloc[col_map.get(type_key, 0)]) or ""
            norm_type = fold_for_comparison(raw_field_type) or ""

            if "multi" in norm_type:
                field_type_code = FieldTypesEnum.MULTI_CHOICE.code
            elif any(
                t in norm_type
                for t in ["sing", "unic", "radio", "dicot", "bool", "categ", "rango"]
            ):
                field_type_code = FieldTypesEnum.SINGLE_CHOICE.code
            else:
                continue

            opt_key = "Texto_opcion" if "Texto_opcion" in col_map else "Opcion"
            raw_option_text = clean_text(row.iloc[col_map.get(opt_key, 0)])
            if raw_option_text is None:
                continue

            ord_key = "Orden_opcion" if "Orden_opcion" in col_map else "Orden"
            raw_order = row.iloc[col_map.get(ord_key, 0)]
            try:
                display_order = int(float(str(raw_order).replace(",", ".")))
            except (ValueError, TypeError):
                display_order = 1

            q_sig = extract_clean_question_number(target_question_label)
            if not q_sig:
                continue

            extracted_choices.append(
                {
                    "year": year,
                    "question_num_key": q_sig,
                    "display_order": display_order,
                    "raw_option_text": raw_option_text,
                }
            )

        logger.debug(
            f"Hoja '{sheet_name}' procesada. Total: {len(extracted_choices)} opciones cargadas."
        )

    return extracted_choices


# -----------------------------------------------------------------------------
# LOOKUPS RELACIONALES CENTRALIZADOS VÍA ORM
# -----------------------------------------------------------------------------


async def get_fields_numeric_lookup(
    conn: AsyncConnection, years: tuple[int, ...]
) -> dict[tuple[int, str], str]:
    """Generates an explicit dictionary lookup linking parsed year and question numbers directly to Field IDs."""
    stmt = (
        select(
            Field.id.label("field_id"),
            Question.label.label("question_label"),
            Form.code.label("form_year"),
        )
        .join(FieldGroup, Field.field_group_id == FieldGroup.id)
        .join(CardTemplate, FieldGroup.card_template_id == CardTemplate.id)
        .join(Question, CardTemplate.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Form, Section.form_id == Form.id)
    )

    lookup = {}
    rows = (await conn.execute(stmt)).mappings().all()
    for r in rows:
        if r["form_year"] is None or r["question_label"] is None:
            continue
        y = int(r["form_year"])
        if y in years:
            q_num = extract_clean_question_number(str(r["question_label"]))
            if q_num:
                lookup[(y, q_num)] = str(r["field_id"])
    return lookup


async def get_existing_field_choices(
    conn: AsyncConnection,
) -> dict[tuple[str, int], dict]:
    stmt = select(
        FieldChoice.id.label("choice_id"),
        FieldChoice.field_id,
        FieldChoice.label,
        FieldChoice.description,
        FieldChoice.display_order,
    )
    rows = (await conn.execute(stmt)).mappings().all()
    return {(str(r["field_id"]), int(r["display_order"])): dict(r) for r in rows}


# -----------------------------------------------------------------------------
# PROCESO CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(FILE_PATH)
    years = get_seeding_active_years()
    if not path.is_file():
        raise FileNotFoundError(f"Archivo estructural Excel no encontrado: {path}")

    logger.debug(f"Iniciando el poblado de forms.field_choices desde {path}...")

    excel = pd.ExcelFile(path)
    raw_choices = load_choices_from_excel(excel, years)

    async with async_engine.begin() as conn:
        db_columns = await get_table_columns(
            conn, schema="forms", table="field_choices"
        )
        validate_required_columns(
            db_columns,
            required={"id", "field_id", "label", "description", "display_order"},
            table_name="forms.field_choices",
        )

        fields_numeric_map = await get_fields_numeric_lookup(conn, years)
        existing_choices = await get_existing_field_choices(conn)

        seen_database_keys = set()
        expected_records = []

        for item in raw_choices:
            y = item["year"]
            q_num = item["question_num_key"]

            field_id_str = fields_numeric_map.get((y, q_num))
            if not field_id_str:
                continue

            choice_unique_key = (field_id_str, int(item["display_order"]))
            if choice_unique_key in seen_database_keys:
                continue
            seen_database_keys.add(choice_unique_key)

            label, description = split_option_text(
                item["raw_option_text"], item["display_order"]
            )
            if not description:
                description = label

            expected_records.append(
                {
                    "natural_key": choice_unique_key,
                    "field_id": field_id_str,
                    "label": label,
                    "description": description,
                    "display_order": item["display_order"],
                }
            )

        inserted, updated = 0, 0

        for source in expected_records:
            old_choice = existing_choices.get(source["natural_key"])
            choice_id = old_choice["choice_id"] if old_choice else new_uuidv7()

            db_payload = {
                "id": choice_id,
                "field_id": source["field_id"],
                "label": truncate_text(
                    source["label"], db_columns["label"]["max_length"]
                ),
                "description": truncate_text(
                    source["description"], db_columns["description"]["max_length"]
                ),
                "updated_at": text("NOW()"),
                "display_order": source["display_order"],
            }

            if old_choice:
                stmt_update = (
                    update(FieldChoice)
                    .where(FieldChoice.id == db_payload["id"])
                    .values(
                        field_id=db_payload["field_id"],
                        label=db_payload["label"],
                        description=db_payload["description"],
                        display_order=db_payload["display_order"],
                    )
                )
                await conn.execute(stmt_update)
                updated += 1
            else:
                stmt_insert = insert(FieldChoice).values(db_payload)
                await conn.execute(stmt_insert)
                inserted += 1

        # -----------------------------------------------------------------------------
        # ASERCIONES DE SANIDAD POST-CARGA
        # -----------------------------------------------------------------------------
        final_stmt = select(
            FieldChoice.id, FieldChoice.field_id, FieldChoice.display_order
        )
        final_rows = [
            dict(r) for r in (await conn.execute(final_stmt)).mappings().all()
        ]

        assert_all_uuidv7(rows=final_rows, id_key="id", label_key="display_order")
        assert_no_duplicates(
            rows=final_rows,
            key_fields=["field_id", "display_order"],
            what="opciones de selección de preguntas (field_choices)",
        )

    logger.info(
        f"Poblado de forms.field_choices finalizado exitosamente. "
        f"Insertados: {inserted}. Actualizados: {updated}. Totales Sincronizados: {len(expected_records)}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
