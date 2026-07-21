"""Puebla forms.field_choices para los IIP 2019, 2021 y 2023.

Dependencia previa:
    11h_seed_fields.py

Convención de almacenamiento:
- label: letra o número corto de la opción.
    Ejemplos: "A", "B", "1", "2".
- description: texto completo de la opción, sin repetir el prefijo cuando el
  texto ya comienza por A., B., 1., 2., etc.
- display_order: Orden_opcion del Excel.
- No se almacenan Valor_maximo ni ponderaciones en description.
- Solo se crean opciones para SINGLE_CHOICE y MULTI_CHOICE.
- Los campos BOOLEAN no usan forms.field_choices.

El script reutiliza la interpretación del instrumento definida en
11h_seed_fields.py para garantizar que las opciones queden asociadas al field
correcto.
"""

from __future__ import annotations

import asyncio
import importlib.util
import re
from collections import defaultdict
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from uuid_utils import uuid7

from shared.infrastructure import async_engine
from shared.utils.logger import get_logger


logger = get_logger("pop/field_choices")
CHOICE_FIELD_TYPES = {"SINGLE_CHOICE", "MULTI_CHOICE"}
EXPECTED_CHOICE_COUNTS = {2019: 46, 2021: 46, 2023: 49}


# -----------------------------------------------------------------------------
# CARGA DE LA LÓGICA COMPARTIDA DE 11h
# -----------------------------------------------------------------------------


def load_fields_module():
    path = Path(__file__).with_name("11h_seed_fields.py")
    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontró {path}. 11i debe estar en la misma carpeta que 11h."
        )

    spec = importlib.util.spec_from_file_location(
        "iip_seed_fields_shared",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No fue posible cargar {path}.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_fields_module()


# -----------------------------------------------------------------------------
# UTILIDADES
# -----------------------------------------------------------------------------


def is_uuidv7(value) -> bool:
    try:
        return UUID(str(value)).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    return str(uuid7())


def parse_option_order(value, context: str) -> int:
    value = H.clean(value)
    if value is None:
        raise ValueError(f"Orden_opcion vacío en {context}.")
    try:
        numeric = float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(
            f"Orden_opcion inválido en {context}: {value!r}"
        ) from exc
    if not numeric.is_integer() or numeric <= 0:
        raise ValueError(
            f"Orden_opcion inválido en {context}: {value!r}"
        )
    return int(numeric)


def split_option(value: str, order: int) -> tuple[str, str]:
    """Separa un prefijo corto de la opción.

    Ejemplos:
        A. Ciudadanía -> ("A", "Ciudadanía")
        10. Completo  -> ("10", "Completo")
        Sí            -> ("1", "Sí")
    """
    value = H.clean(value)
    if value is None:
        raise ValueError("Texto_opcion vacío.")

    match = re.match(
        r"^\s*([A-Za-z]|\d+(?:[.,]\d+)*)\s*[\.)]\s*(.*)$",
        value,
    )
    if match:
        code = match.group(1).replace(",", ".").upper()
        description = H.clean(match.group(2))
        if description:
            return code, description

    return str(order), value


# -----------------------------------------------------------------------------
# CONSTRUCCIÓN DE OPCIONES
# -----------------------------------------------------------------------------


def build_choice_specs(field_specs: list[dict]) -> list[dict]:
    choices: list[dict] = []

    for field in field_specs:
        if field["field_type_label"] not in CHOICE_FIELD_TYPES:
            continue

        option_rows = [
            row
            for row in field["option_rows"]
            if H.clean(row["option_text"]) is not None
        ]
        if not option_rows:
            raise ValueError(
                f"El field de selección {field['year']} / "
                f"{field['question_code']} / {field['group_kind']} / "
                f"orden {field['display_order']} no tiene Texto_opcion."
            )

        seen_orders = set()
        for row in option_rows:
            order = parse_option_order(
                row["option_order"],
                f"{row['source_sheet']} fila {row['source_row']}",
            )
            if order in seen_orders:
                raise ValueError(
                    f"Orden_opcion {order} repetido para "
                    f"{field['year']} / {field['question_code']} / "
                    f"field {field['display_order']}."
                )
            seen_orders.add(order)

            label, description = split_option(
                row["option_text"],
                order,
            )

            choices.append(
                {
                    "year": field["year"],
                    "question_code": field["question_code"],
                    "group_kind": field["group_kind"],
                    "field_display_order": int(field["display_order"]),
                    "field_type_label": field["field_type_label"],
                    "display_order": order,
                    "label": label,
                    "description": description,
                }
            )

    counts = defaultdict(int)
    for choice in choices:
        counts[choice["year"]] += 1

    if dict(counts) != EXPECTED_CHOICE_COUNTS:
        raise ValueError(
            f"Conteos de field_choices inesperados. Esperado="
            f"{EXPECTED_CHOICE_COUNTS}; obtenido={dict(counts)}"
        )

    return choices


# -----------------------------------------------------------------------------
# POSTGRESQL
# -----------------------------------------------------------------------------


async def get_existing_choices(conn) -> dict[tuple[str, int], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                id::text AS choice_id,
                field_id::text AS field_id,
                label,
                description,
                display_order
            FROM forms.field_choices
            ORDER BY field_id, display_order, id;
            """
        )
    )

    grouped: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[
            (row["field_id"], int(row["display_order"]))
        ].append(dict(row))

    lookup: dict[tuple[str, int], dict] = {}
    for key, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                f"field_choices duplicados para field/orden {key}: "
                f"{[row['choice_id'] for row in rows]}"
            )
        if not is_uuidv7(rows[0]["choice_id"]):
            raise ValueError(
                f"field_choice existente no UUIDv7: {rows[0]['choice_id']}"
            )
        lookup[key] = rows[0]

    return lookup


async def save_choice(conn, record: dict, update: bool) -> None:
    if update:
        statement = text(
            """
            UPDATE forms.field_choices
            SET
                field_id = CAST(:field_id AS uuid),
                label = :label,
                description = :description,
                display_order = :display_order,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
            """
        )
    else:
        statement = text(
            """
            INSERT INTO forms.field_choices (
                id,
                field_id,
                label,
                description,
                display_order,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:field_id AS uuid),
                :label,
                :description,
                :display_order,
                NOW()
            );
            """
        )
    await conn.execute(statement, record)


# -----------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade(gh=None, api=None) -> None:
    del gh, api

    path = Path(H.FILE_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    logger.info(f"Starting forms.field_choices population from {path}")

    main_questions, loops, responses, field_specs = H.load_instrument(path)
    choice_specs = build_choice_specs(field_specs)

    async with async_engine.begin() as conn:
        columns = await H.table_columns(conn, "forms", "field_choices")
        required_columns = {
            "id",
            "field_id",
            "label",
            "description",
            "display_order",
            "updated_at",
        }
        missing = required_columns - set(columns)
        if missing:
            raise ValueError(
                f"Faltan columnas en forms.field_choices: {sorted(missing)}"
            )

        questions = await H.get_questions(conn, main_questions, loops)
        direct_groups, card_groups = await H.get_groups(
            conn,
            questions,
            main_questions,
            loops,
        )
        field_map = await H.get_field_map_for_specs(
            conn,
            field_specs,
            direct_groups,
            card_groups,
        )
        existing = await get_existing_choices(conn)

        inserted = 0
        updated = 0

        for source in choice_specs:
            field_key = (
                source["year"],
                source["question_code"],
                source["group_kind"],
                int(source["field_display_order"]),
            )
            field = field_map.get(field_key)
            if field is None:
                raise ValueError(
                    f"No se encontró forms.fields para {field_key}. "
                    "Ejecuta antes 11h_seed_fields.py."
                )
            if field["field_type_label"] != source["field_type_label"]:
                raise ValueError(
                    f"Tipo de field incorrecto para {field_key}: "
                    f"SQL={field['field_type_label']}; "
                    f"Excel={source['field_type_label']}."
                )

            natural_key = (
                field["field_id"],
                int(source["display_order"]),
            )
            old = existing.get(natural_key)

            choice_id = old["choice_id"] if old else new_uuidv7()
            if not is_uuidv7(choice_id):
                raise ValueError(f"ID no UUIDv7: {choice_id}")

            db_record = {
                "id": choice_id,
                "field_id": field["field_id"],
                "label": H.truncate(
                    source["label"], columns["label"]["max_length"]
                ),
                "description": H.truncate(
                    source["description"],
                    columns["description"]["max_length"],
                ),
                "display_order": int(source["display_order"]),
            }

            await save_choice(conn, db_record, update=old is not None)
            if old:
                updated += 1
            else:
                inserted += 1

        # Validación focalizada sobre las opciones esperadas.
        reloaded = await get_existing_choices(conn)
        for source in choice_specs:
            field_key = (
                source["year"],
                source["question_code"],
                source["group_kind"],
                int(source["field_display_order"]),
            )
            field = field_map[field_key]
            choice_key = (
                field["field_id"],
                int(source["display_order"]),
            )
            row = reloaded.get(choice_key)
            if row is None:
                raise ValueError(f"No se cargó field_choice {choice_key}.")
            if H.normalize_text(row["label"]) != H.normalize_text(
                source["label"]
            ):
                raise ValueError(f"label incorrecto para {choice_key}.")
            if H.normalize_text(row["description"]) != H.normalize_text(
                source["description"]
            ):
                raise ValueError(f"description incorrecta para {choice_key}.")
            if not is_uuidv7(row["choice_id"]):
                raise ValueError(f"UUID no es versión 7 para {choice_key}.")

        invalid = await conn.execute(
            text(
                """
                SELECT COUNT(*) AS total
                FROM forms.field_choices choice
                JOIN forms.fields field
                  ON field.id = choice.field_id
                JOIN reference.field_types field_type
                  ON field_type.id = field.field_type_id
                WHERE UPPER(TRIM(field_type.label))
                      NOT IN ('SINGLE_CHOICE', 'MULTI_CHOICE');
                """
            )
        )
        if int(invalid.scalar_one()) != 0:
            raise ValueError(
                "Hay field_choices asociados a fields que no son de selección."
            )

    logger.info(
        "forms.field_choices population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}. "
        f"Expected: {len(choice_specs)}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
