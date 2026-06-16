"""Puebla forms.field_choices para los IIP 2019, 2021 y 2023.

Debe ejecutarse después de 11h_seed_fields.py. Para garantizar que la lógica de
campos y opciones sea idéntica, este archivo reutiliza las funciones puras de
11h mediante importlib. No depende de helpers de preguntas, grupos o tarjetas.
"""

from __future__ import annotations

import asyncio
import importlib.util
import math
from collections import defaultdict
from pathlib import Path

from sqlalchemy import text
from uuid_utils import uuid7

from shared_db import async_engine
from shared_utils.logger import get_logger


logger = get_logger("pop/field_choices")
CHOICE_TYPES = {"SINGLE_CHOICE", "MULTI_CHOICE"}
OPTIONAL_SCORE_COLUMNS = ("maximum_value", "max_value", "score", "weight")


def load_fields_module():
    path = Path(__file__).with_name("11h_seed_fields.py")
    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontró {path}. 11i requiere el 11h corregido en la misma carpeta."
        )
    spec = importlib.util.spec_from_file_location("iip_seed_fields_shared", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No fue posible cargar {path}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_fields_module()


def parse_option_order(value, context: str) -> int:
    value = H.clean(value)
    if value is None:
        raise ValueError(f"Orden_opcion vacío en {context}.")
    try:
        numeric = float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Orden_opcion inválido en {context}: {value!r}") from exc
    if not numeric.is_integer() or numeric <= 0:
        raise ValueError(f"Orden_opcion inválido en {context}: {value!r}")
    return int(numeric)


def parse_score(value):
    value = H.clean(value)
    if value is None:
        return None
    try:
        return float(value.replace(" ", "").replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Valor_maximo inválido: {value!r}") from exc


def build_choice_specs(field_specs, responses):
    """Añade las opciones a cada field de selección usando su fila fuente."""
    # Índice de grupos de respuesta por (año, pregunta, fila inicial).
    response_groups = {}
    for year, by_question in responses.items():
        for question_code, rows in by_question.items():
            for group in H.group_rows_by_subquestion(rows):
                definition = H.choose_definition(group)
                response_groups[
                    (year, question_code, int(definition["source_row_first"]))
                ] = definition["rows"]

    choices = []
    for field in field_specs:
        if field["field_type_label"] not in CHOICE_TYPES:
            continue

        key = (
            field["year"],
            field.get("response_question_code", field["question_code"]),
            int(field["source_row_first"]),
        )
        rows = response_groups.get(key)
        if not rows:
            raise ValueError(
                f"No se encontraron filas fuente para las opciones de {key}."
            )

        option_rows = [row for row in rows if H.clean(row["option_text"]) is not None]
        if not option_rows:
            raise ValueError(
                f"El field de selección {key} no tiene Texto_opcion."
            )

        seen_orders = set()
        for row in option_rows:
            order = parse_option_order(
                row["option_order"],
                f"{row['source_sheet']} fila {row['source_row']}",
            )
            if order in seen_orders:
                raise ValueError(
                    f"Orden_opcion {order} repetido para {key}."
                )
            seen_orders.add(order)
            choices.append(
                {
                    "year": field["year"],
                    "question_code": field["question_code"],
                    "group_kind": field["group_kind"],
                    "field_display_order": int(field["display_order"]),
                    "field_type_label": field["field_type_label"],
                    "display_order": order,
                    "label": row["option_text"],
                    "maximum_value": parse_score(row["maximum_value"]),
                    "source_sheet": row["source_sheet"],
                    "source_row": int(row["source_row"]),
                }
            )

    expected_by_year = {2019: 46, 2021: 46, 2023: 49}
    actual_by_year = defaultdict(int)
    for choice in choices:
        actual_by_year[choice["year"]] += 1

    if dict(actual_by_year) != expected_by_year:
        raise ValueError(
            f"Conteos de field_choices inesperados. "
            f"Esperado={expected_by_year}; obtenido={dict(actual_by_year)}"
        )

    return choices


async def get_choice_table_columns(conn):
    columns = await H.table_columns(conn, "forms", "field_choices")
    required = {
        "id", "field_id", "label", "description", "display_order", "updated_at"
    }
    missing = required - set(columns)
    if missing:
        raise ValueError(f"Faltan columnas en forms.field_choices: {sorted(missing)}")

    score_column = None
    for candidate in OPTIONAL_SCORE_COLUMNS:
        if candidate in columns:
            score_column = candidate
            break
    return columns, score_column


async def load_field_map(conn, main_questions, loops):
    """Obtiene field_id por año, código, tipo de grupo y display_order."""
    result = await conn.execute(
        text(
            """
            SELECT fld.id::text field_id,
                   fld.display_order field_display_order,
                   UPPER(TRIM(ft.label)) field_type_label,
                   fg.card_template_id::text card_template_id,
                   q.label question_label,
                   f.anno
            FROM forms.fields fld
            JOIN reference.field_types ft ON ft.id=fld.field_type_id
            JOIN forms.field_groups fg ON fg.id=fld.field_group_id
            JOIN forms.questions q ON q.id=fg.question_id
            JOIN forms.forms f ON f.id=fld.form_id
            WHERE f.anno IN (2019,2021,2023)
            ORDER BY f.anno, q.label, fg.card_template_id, fld.display_order;
            """
        )
    )

    expected_labels = {
        (year, H.normalize_text(item["raw_code"]))
        for year, items in main_questions.items()
        for item in items
    }
    expected_labels.update((2023, H.normalize_text(code)) for code in loops)

    field_map = {}
    for row in result.mappings().all():
        year = int(row["anno"])
        question_key = (year, H.normalize_text(row["question_label"]))
        if question_key not in expected_labels:
            continue
        group_kind = "DIRECT" if row["card_template_id"] is None else "CARD"
        key = (
            year,
            H.clean(row["question_label"]),
            group_kind,
            int(row["field_display_order"]),
        )
        # Se reindexa también por label normalizado para evitar diferencias de mayúsculas.
        normalized_key = (
            year,
            H.normalize_text(row["question_label"]),
            group_kind,
            int(row["field_display_order"]),
        )
        if normalized_key in field_map:
            raise ValueError(f"Field duplicado para {normalized_key}.")
        field_map[normalized_key] = {
            "field_id": row["field_id"],
            "field_type_label": row["field_type_label"],
        }

    return field_map


async def load_existing_choices(conn):
    result = await conn.execute(
        text(
            """
            SELECT id::text id, field_id::text field_id,
                   label, description, display_order
            FROM forms.field_choices;
            """
        )
    )
    by_key = defaultdict(list)
    for row in result.mappings().all():
        row = dict(row)
        by_key[(row["field_id"], int(row["display_order"]))].append(row)
    return by_key


def choice_description(choice, max_length):
    score = (
        "pendiente"
        if choice["maximum_value"] is None
        else format(float(choice["maximum_value"]), ".15g")
    )
    value = (
        f"Fuente: {choice['source_sheet']}, fila {choice['source_row']}. "
        f"Valor máximo: {score}."
    )
    return H.truncate(value, max_length)


async def save_choices(conn, choices, field_map, columns, score_column):
    existing_by_key = await load_existing_choices(conn)
    inserted = 0
    updated = 0

    for choice in choices:
        field_key = (
            choice["year"],
            H.normalize_text(choice["question_code"]),
            choice["group_kind"],
            int(choice["field_display_order"]),
        )
        field = field_map.get(field_key)
        if field is None:
            raise ValueError(
                f"No se encontró forms.fields para {field_key}. "
                "Ejecuta primero el 11h corregido."
            )
        if field["field_type_label"] != choice["field_type_label"]:
            raise ValueError(
                f"Tipo incorrecto para {field_key}: SQL={field['field_type_label']}; "
                f"Excel={choice['field_type_label']}"
            )

        field_id = field["field_id"]
        key = (field_id, int(choice["display_order"]))
        existing = existing_by_key.get(key, [])
        if len(existing) > 1:
            raise ValueError(f"field_choices duplicados para field/orden {key}.")

        choice_id = existing[0]["id"] if existing else str(uuid7())
        params = {
            "id": choice_id,
            "field_id": field_id,
            "label": H.truncate(choice["label"], columns["label"]["max_length"]),
            "description": choice_description(
                choice, columns["description"]["max_length"]
            ),
            "display_order": int(choice["display_order"]),
            "score": choice["maximum_value"],
        }

        score_set = f", {score_column}=:score" if score_column else ""
        score_insert_column = f", {score_column}" if score_column else ""
        score_insert_value = ", :score" if score_column else ""

        if existing:
            await conn.execute(
                text(
                    f"""
                    UPDATE forms.field_choices
                    SET field_id=CAST(:field_id AS uuid), label=:label,
                        description=:description, display_order=:display_order,
                        updated_at=NOW(){score_set}
                    WHERE id=CAST(:id AS uuid);
                    """
                ),
                params,
            )
            updated += 1
        else:
            await conn.execute(
                text(
                    f"""
                    INSERT INTO forms.field_choices
                        (id, field_id, label, description, display_order,
                         updated_at{score_insert_column})
                    VALUES
                        (CAST(:id AS uuid), CAST(:field_id AS uuid),
                         :label, :description, :display_order,
                         NOW(){score_insert_value});
                    """
                ),
                params,
            )
            inserted += 1

    return inserted, updated


async def validate_choices(conn):
    result = await conn.execute(
        text(
            """
            SELECT f.anno, COUNT(*) total
            FROM forms.field_choices fc
            JOIN forms.fields fld ON fld.id=fc.field_id
            JOIN forms.forms f ON f.id=fld.form_id
            WHERE f.anno IN (2019,2021,2023)
            GROUP BY f.anno ORDER BY f.anno;
            """
        )
    )
    actual = {int(row["anno"]): int(row["total"]) for row in result.mappings().all()}
    expected = {2019: 46, 2021: 46, 2023: 49}
    if actual != expected:
        raise ValueError(
            f"Validación de forms.field_choices falló. "
            f"Esperado={expected}; obtenido={actual}"
        )

    invalid = await conn.execute(
        text(
            """
            SELECT COUNT(*) total
            FROM forms.field_choices fc
            JOIN forms.fields fld ON fld.id=fc.field_id
            JOIN reference.field_types ft ON ft.id=fld.field_type_id
            JOIN forms.forms f ON f.id=fld.form_id
            WHERE f.anno IN (2019,2021,2023)
              AND UPPER(TRIM(ft.label)) NOT IN ('SINGLE_CHOICE','MULTI_CHOICE');
            """
        )
    )
    if int(invalid.scalar_one()) != 0:
        raise ValueError("Hay field_choices asociados a fields no seleccionables.")


async def upgrade(gh=None, api=None) -> None:
    del gh, api
    path = H.resolve_excel_path()
    logger.info(f"[11i] Archivo: {path}")
    print(f"[11i] Archivo Excel: {path}", flush=True)

    excel = H.pd.ExcelFile(path)
    main_questions, loops = H.load_structure(excel)
    responses = H.load_response_groups(excel)
    field_specs = H.build_field_specs(main_questions, loops, responses)
    choices = build_choice_specs(field_specs, responses)

    print(
        f"[11i] Opciones construidas: 2019=46, 2021=46, 2023=49, "
        f"total={len(choices)}",
        flush=True,
    )

    async with async_engine.begin() as conn:
        columns, score_column = await get_choice_table_columns(conn)
        field_map = await load_field_map(conn, main_questions, loops)
        inserted, updated = await save_choices(
            conn, choices, field_map, columns, score_column
        )
        await validate_choices(conn)

    logger.info(
        f"[11i] forms.field_choices completado. "
        f"Insertados={inserted}; actualizados={updated}."
    )
    print(
        f"[11i] OK. Insertados={inserted}; actualizados={updated}; total=141.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
