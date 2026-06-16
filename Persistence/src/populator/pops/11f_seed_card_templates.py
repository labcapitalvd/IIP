"""Puebla forms.card_templates para las preguntas tipo bucle del IIP 2023.

Dependencias previas:
    11d_seed_questions.py
    11e_seed_loop_questions.py

Modelo utilizado:
    forms.card_templates.question_id -> forms.questions.id

La tabla forms.card_templates del proyecto contiene:
    question_id, label, description, helper, updated_at, id

Reglas:
- Se crea una plantilla de tarjeta por cada pregunta administrada con is_loop=TRUE.
- Incluye los 26 bucles independientes y la pregunta mixta Pregunta 28.1.
- Pregunta 28.1 reutiliza el mismo question_id de la pregunta principal.
- Los registros nuevos usan UUID versión 7.
- Las ejecuciones posteriores conservan el UUID existente y actualizan contenido.
- No se crean min_cards, max_cards ni display_order porque esas columnas no
  existen en el modelo actual de forms.card_templates.
- No se eliminan automáticamente plantillas antiguas para evitar romper
  relaciones con field_groups o respuestas.
"""

import json
import os
from collections import defaultdict
from uuid import UUID

from sqlalchemy import text
from uuid_utils import uuid7

from shared_db import async_engine
from shared_utils.logger import get_logger


logger = get_logger("pop/card_templates")

YEAR = 2023
CURRENT_SOURCE = "Estructura_IIP.xlsx"
VALID_SOURCES = {
    "Estructura IIP.xlsx",
    "Estructura_IIP.xlsx",
}
EXPECTED_LOOP_COUNT = int(
    os.getenv("IIP_EXPECTED_2023_LOOP_COUNT", "27")
)
EXPECTED_MIXED_COUNT = int(
    os.getenv("IIP_EXPECTED_2023_MIXED_LOOP_COUNT", "1")
)


# ---------------------------------------------------------------------
# FUNCIONES GENERALES
# ---------------------------------------------------------------------


def clean(value):
    """Convierte valores vacíos en None."""
    if value is None:
        return None

    value = str(value).strip()
    return value or None


def parse_helper(value):
    """Convierte helper JSON a diccionario."""
    value = clean(value)

    if value is None:
        return None

    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None

    return parsed if isinstance(parsed, dict) else None


def is_uuidv7(value) -> bool:
    """Valida UUID versión 7."""
    try:
        return UUID(str(value)).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    """Genera UUID versión 7."""
    return str(uuid7())


def truncate(value, max_length):
    """Recorta texto únicamente si la columna tiene longitud máxima."""
    value = clean(value)

    if value is None or max_length is None:
        return value

    return value[:max_length]


def is_managed_question_helper(helper: dict | None) -> bool:
    """Indica si una pregunta fue generada por los pobladores del IIP."""
    if not helper:
        return False

    return (
        helper.get("entity") == "forms.questions"
        and helper.get("source") in VALID_SOURCES
    )


def is_managed_card_helper(helper: dict | None) -> bool:
    """Indica si una plantilla fue generada por este poblador."""
    if not helper:
        return False

    return (
        helper.get("entity") == "forms.card_templates"
        and helper.get("source") in VALID_SOURCES
    )


# ---------------------------------------------------------------------
# METADATOS DE POSTGRESQL
# ---------------------------------------------------------------------


async def get_table_columns(conn) -> dict:
    """Consulta la definición real de forms.card_templates."""
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'forms'
              AND table_name = 'card_templates'
            ORDER BY ordinal_position;
            """
        )
    )

    rows = result.mappings().all()

    if not rows:
        raise ValueError(
            "No se encontró la tabla forms.card_templates en PostgreSQL."
        )

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_required_columns(columns: dict) -> None:
    """Valida las columnas requeridas por el modelo actual."""
    required = {
        "id",
        "question_id",
        "label",
        "description",
        "helper",
        "updated_at",
    }

    missing = required - set(columns)

    if missing:
        raise ValueError(
            "La tabla forms.card_templates no tiene todas las columnas "
            f"requeridas. Faltan: {sorted(missing)}"
        )


# ---------------------------------------------------------------------
# PREGUNTAS TIPO BUCLE
# ---------------------------------------------------------------------


async def get_loop_questions(conn) -> list[dict]:
    """Obtiene las preguntas tipo bucle que necesitan card_template.

    Incluye:
    - bucles independientes: is_main_question=False, is_loop=True;
    - pregunta mixta 28.1: is_main_question=True, is_loop=True.
    """
    result = await conn.execute(
        text(
            """
            SELECT
                q.id::text AS question_id,
                q.form_id::text AS form_id,
                q.section_id::text AS section_id,
                q.label,
                q.description,
                q.helper,
                q.is_loop,
                f.anno
            FROM forms.questions q
            JOIN forms.forms f
                ON f.id = q.form_id
            WHERE f.anno = :year
              AND q.is_loop = TRUE
            ORDER BY q.display_order, q.id;
            """
        ),
        {"year": YEAR},
    )

    records = []
    natural_keys = set()

    for row in result.mappings().all():
        helper = parse_helper(row["helper"])

        # No se intervienen preguntas ajenas a este proceso.
        if not is_managed_question_helper(helper):
            continue

        if not is_uuidv7(row["question_id"]):
            raise ValueError(
                "La pregunta tipo bucle no tiene UUIDv7: "
                f"{row['question_id']}"
            )

        if not is_uuidv7(row["form_id"]):
            raise ValueError(
                f"El form_id de la pregunta {row['question_id']} no es UUIDv7."
            )

        loop_definition = helper.get("loop_definition")

        if not isinstance(loop_definition, dict):
            raise ValueError(
                f"La pregunta {row['label']} ({row['question_id']}) tiene "
                "is_loop=TRUE, pero no contiene loop_definition en helper. "
                "Ejecuta antes 11e_seed_loop_questions.py."
            )

        question_code = clean(
            loop_definition.get("question_code")
            or helper.get("question_code")
        )
        question_raw_code = clean(
            loop_definition.get("question_raw_code")
            or helper.get("question_raw_code")
            or row["label"]
        )
        indicator_code = clean(helper.get("indicator_code"))
        question_uid = clean(
            helper.get("question_uid")
            or helper.get("natural_key")
        )

        if question_code is None:
            raise ValueError(
                f"No se encontró question_code para {row['question_id']}."
            )

        if indicator_code is None:
            raise ValueError(
                f"No se encontró indicator_code para {row['question_id']}."
            )

        subquestions = loop_definition.get("subquestions")

        if not isinstance(subquestions, list) or not subquestions:
            raise ValueError(
                f"El bucle {question_raw_code} no tiene subquestions válidas."
            )

        declared_count = loop_definition.get("subquestion_count")

        if declared_count is not None and int(declared_count) != len(subquestions):
            raise ValueError(
                f"El bucle {question_raw_code} declara {declared_count} "
                f"subpreguntas, pero contiene {len(subquestions)}."
            )

        is_main_question = helper.get("is_main_question") is True
        is_mixed_question = helper.get("is_mixed_question") is True

        if is_mixed_question and not is_main_question:
            raise ValueError(
                f"El bucle mixto {question_raw_code} debe conservar "
                "is_main_question=TRUE."
            )

        parent_question_id = clean(
            loop_definition.get("parent_question_id")
            or helper.get("parent_question_id")
        )

        if is_mixed_question:
            if parent_question_id is not None:
                raise ValueError(
                    f"El bucle mixto {question_raw_code} no debe tener "
                    "parent_question_id."
                )
        elif not is_uuidv7(parent_question_id):
            raise ValueError(
                f"El bucle {question_raw_code} no tiene un "
                "parent_question_id UUIDv7 válido."
            )

        natural_key = (
            YEAR,
            indicator_code,
            question_code,
        )

        if natural_key in natural_keys:
            raise ValueError(
                f"Hay preguntas tipo bucle duplicadas para {natural_key}."
            )

        natural_keys.add(natural_key)

        records.append(
            {
                "year": YEAR,
                "question_id": row["question_id"],
                "form_id": row["form_id"],
                "section_id": row["section_id"],
                "question_label": row["label"],
                "question_description": row["description"],
                "question_code": question_code,
                "question_raw_code": question_raw_code,
                "question_uid": question_uid,
                "indicator_code": indicator_code,
                "is_main_question": is_main_question,
                "is_mixed_question": is_mixed_question,
                "parent_question_id": parent_question_id,
                "parent_question_code": clean(
                    loop_definition.get("parent_question_code")
                    or helper.get("parent_question_code")
                ),
                "parent_question_raw_code": clean(
                    loop_definition.get("parent_question_raw_code")
                    or helper.get("parent_question_raw_code")
                ),
                "loop_text": clean(loop_definition.get("text"))
                or clean(row["description"]),
                "loop_weight": loop_definition.get("weight"),
                "subquestion_count": len(subquestions),
                "subquestion_orders": [
                    item.get("order")
                    for item in subquestions
                    if isinstance(item, dict)
                ],
                "source_sheet": clean(
                    loop_definition.get("source_sheet")
                ) or "2023",
                "response_sheet": clean(
                    loop_definition.get("response_sheet")
                ) or "Respuestas_2023",
            }
        )

    if len(records) != EXPECTED_LOOP_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_LOOP_COUNT} preguntas tipo bucle "
            f"administradas para {YEAR}, pero se encontraron {len(records)}. "
            "Revisa la ejecución de 11d_seed_questions.py y "
            "11e_seed_loop_questions.py."
        )

    mixed_count = sum(
        1 for record in records if record["is_mixed_question"]
    )

    if mixed_count != EXPECTED_MIXED_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_MIXED_COUNT} preguntas mixtas para "
            f"{YEAR}, pero se encontraron {mixed_count}."
        )

    return records


# ---------------------------------------------------------------------
# PLANTILLAS EXISTENTES
# ---------------------------------------------------------------------


async def get_existing_templates(conn) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """Obtiene plantillas existentes agrupadas por question_id.

    Retorna:
        managed_by_question:
            question_id -> plantilla administrada

        unmanaged_by_question:
            question_id -> plantillas no administradas
    """
    result = await conn.execute(
        text(
            """
            SELECT
                ct.id::text AS card_template_id,
                ct.question_id::text AS question_id,
                ct.label,
                ct.description,
                ct.helper,
                f.anno
            FROM forms.card_templates ct
            JOIN forms.questions q
                ON q.id = ct.question_id
            JOIN forms.forms f
                ON f.id = q.form_id
            WHERE f.anno = :year
            ORDER BY ct.question_id, ct.id;
            """
        ),
        {"year": YEAR},
    )

    managed_by_question = {}
    unmanaged_by_question = defaultdict(list)

    for row in result.mappings().all():
        helper = parse_helper(row["helper"])
        row_dict = dict(row)

        if is_managed_card_helper(helper):
            question_id = row["question_id"]

            if question_id in managed_by_question:
                raise ValueError(
                    "Existen varias plantillas administradas para la "
                    f"pregunta {question_id}: "
                    f"{managed_by_question[question_id]['card_template_id']} "
                    f"y {row['card_template_id']}."
                )

            if not is_uuidv7(row["card_template_id"]):
                raise ValueError(
                    "La plantilla existente no tiene UUIDv7: "
                    f"{row['card_template_id']}"
                )

            row_dict["helper_dict"] = helper
            managed_by_question[question_id] = row_dict
        else:
            unmanaged_by_question[row["question_id"]].append(row_dict)

    return managed_by_question, dict(unmanaged_by_question)


# ---------------------------------------------------------------------
# CONSTRUCCIÓN DE REGISTROS
# ---------------------------------------------------------------------


def make_label(record: dict) -> str:
    """Construye un label corto y estable para la tarjeta."""
    raw_code = (
        clean(record["question_raw_code"])
        or record["question_code"]
    )

    return f"Registro - {raw_code}"


def make_description(record: dict) -> str:
    """Usa el enunciado del bucle como descripción de la plantilla."""
    return (
        clean(record["loop_text"])
        or clean(record["question_description"])
        or f"Plantilla repetible para {record['question_raw_code']}."
    )


def make_helper(record: dict, card_template_id: str) -> str:
    """Construye helper técnico compacto para la plantilla."""
    natural_key = f"{YEAR}|{record['question_id']}|CARD_TEMPLATE"

    helper = {
        "source": CURRENT_SOURCE,
        "source_version": 1,
        "entity": "forms.card_templates",
        "year": YEAR,
        "card_template_id": card_template_id,
        "card_template_uid": natural_key,
        "natural_key": natural_key,
        "question_id": record["question_id"],
        "question_uid": record["question_uid"],
        "question_code": record["question_code"],
        "question_raw_code": record["question_raw_code"],
        "indicator_code": record["indicator_code"],
        "is_main_question": record["is_main_question"],
        "is_mixed_question": record["is_mixed_question"],
        "parent_question_id": record["parent_question_id"],
        "parent_question_code": record["parent_question_code"],
        "parent_question_raw_code": record["parent_question_raw_code"],
        "loop_weight": record["loop_weight"],
        "subquestion_count": record["subquestion_count"],
        "subquestion_orders": record["subquestion_orders"],
        "source_sheet": record["source_sheet"],
        "response_sheet": record["response_sheet"],
    }

    return json.dumps(
        helper,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def prepare_db_record(
    source_record: dict,
    columns: dict,
    existing: dict | None,
) -> dict:
    """Prepara INSERT o UPDATE de forms.card_templates."""
    card_template_id = (
        existing["card_template_id"]
        if existing
        else new_uuidv7()
    )

    if not is_uuidv7(card_template_id):
        raise ValueError(
            f"El ID de card_template no es UUIDv7: {card_template_id}"
        )

    full_label = make_label(source_record)
    label = truncate(
        full_label,
        columns["label"]["max_length"],
    )

    if label is None:
        raise ValueError(
            "No fue posible construir label para la plantilla de "
            f"{source_record['question_raw_code']}."
        )

    description = truncate(
        make_description(source_record),
        columns["description"]["max_length"],
    )

    if description is None and not columns["description"]["nullable"]:
        description = full_label

    helper = make_helper(
        source_record,
        card_template_id,
    )
    helper_max = columns["helper"]["max_length"]

    if helper_max is not None and len(helper) > helper_max:
        raise ValueError(
            "El helper de la plantilla para "
            f"{source_record['question_raw_code']} tiene {len(helper)} "
            f"caracteres y supera el máximo de {helper_max}."
        )

    return {
        "id": card_template_id,
        "question_id": source_record["question_id"],
        "label": label,
        "description": description,
        "helper": helper,
    }


async def insert_template(conn, record: dict) -> None:
    """Inserta una plantilla nueva."""
    await conn.execute(
        text(
            """
            INSERT INTO forms.card_templates (
                id,
                question_id,
                label,
                description,
                helper,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:question_id AS uuid),
                :label,
                :description,
                :helper,
                NOW()
            );
            """
        ),
        record,
    )


async def update_template(conn, record: dict) -> None:
    """Actualiza una plantilla conservando su UUID."""
    await conn.execute(
        text(
            """
            UPDATE forms.card_templates
            SET
                question_id = CAST(:question_id AS uuid),
                label = :label,
                description = :description,
                helper = :helper,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
            """
        ),
        record,
    )


# ---------------------------------------------------------------------
# VALIDACIÓN POSTERIOR
# ---------------------------------------------------------------------


async def validate_loaded_templates(
    conn,
    expected_questions: list[dict],
) -> None:
    """Valida cardinalidad, FK, UUIDv7 y pregunta mixta."""
    expected_question_ids = {
        record["question_id"]
        for record in expected_questions
    }

    result = await conn.execute(
        text(
            """
            SELECT
                ct.id::text AS card_template_id,
                ct.question_id::text AS question_id,
                ct.helper AS card_helper,
                q.helper AS question_helper,
                q.is_loop,
                f.anno
            FROM forms.card_templates ct
            JOIN forms.questions q
                ON q.id = ct.question_id
            JOIN forms.forms f
                ON f.id = q.form_id
            WHERE f.anno = :year
            ORDER BY ct.question_id, ct.id;
            """
        ),
        {"year": YEAR},
    )

    loaded = {}

    for row in result.mappings().all():
        card_helper = parse_helper(row["card_helper"])

        if not is_managed_card_helper(card_helper):
            continue

        question_id = row["question_id"]

        if question_id not in expected_question_ids:
            continue

        if question_id in loaded:
            raise ValueError(
                f"La pregunta {question_id} tiene más de una plantilla "
                "administrada."
            )

        if not is_uuidv7(row["card_template_id"]):
            raise ValueError(
                "La plantilla no tiene UUIDv7: "
                f"{row['card_template_id']}"
            )

        if row["is_loop"] is not True:
            raise ValueError(
                f"La plantilla {row['card_template_id']} está asociada "
                "a una pregunta con is_loop distinto de TRUE."
            )

        if clean(card_helper.get("question_id")) != question_id:
            raise ValueError(
                f"El helper de {row['card_template_id']} contiene un "
                "question_id diferente a la FK real."
            )

        question_helper = parse_helper(row["question_helper"])

        if not is_managed_question_helper(question_helper):
            raise ValueError(
                f"La plantilla {row['card_template_id']} apunta a una "
                "pregunta no administrada por el proceso IIP."
            )

        loaded[question_id] = dict(row)

    missing = expected_question_ids - set(loaded)

    if missing:
        raise ValueError(
            "No se cargaron plantillas para todas las preguntas tipo bucle. "
            f"Question IDs faltantes: {sorted(missing)[:20]}"
        )

    mixed_templates = 0

    for row in loaded.values():
        helper = parse_helper(row["card_helper"]) or {}

        if helper.get("is_mixed_question") is True:
            mixed_templates += 1

    if mixed_templates != EXPECTED_MIXED_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_MIXED_COUNT} plantillas mixtas y se "
            f"validaron {mixed_templates}."
        )

    logger.info(
        "forms.card_templates validation passed successfully. "
        f"Validated templates: {len(loaded)}."
    )


# ---------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------------------------------------------------


async def upgrade(gh, api) -> None:
    """Puebla forms.card_templates para los bucles de 2023."""
    del gh
    del api

    logger.info(
        "Starting forms.card_templates population for IIP 2023..."
    )

    try:
        async with async_engine.begin() as conn:
            columns = await get_table_columns(conn)
            validate_required_columns(columns)

            loop_questions = await get_loop_questions(conn)

            managed_existing, unmanaged_existing = (
                await get_existing_templates(conn)
            )

            target_question_ids = {
                record["question_id"]
                for record in loop_questions
            }

            conflicting_unmanaged = {
                question_id: rows
                for question_id, rows in unmanaged_existing.items()
                if question_id in target_question_ids
            }

            if conflicting_unmanaged:
                sample = {
                    question_id: [
                        row["card_template_id"] for row in rows
                    ]
                    for question_id, rows in list(
                        conflicting_unmanaged.items()
                    )[:10]
                }

                raise ValueError(
                    "Existen card_templates no administrados para preguntas "
                    "tipo bucle del IIP. No se insertarán duplicados de forma "
                    f"automática. Muestra: {sample}"
                )

            stale_question_ids = (
                set(managed_existing)
                - target_question_ids
            )

            if stale_question_ids:
                logger.warning(
                    "Existen plantillas administradas de versiones anteriores "
                    "que ya no corresponden a una pregunta tipo bucle actual. "
                    "No se eliminan automáticamente. "
                    f"Total: {len(stale_question_ids)}. "
                    f"Muestra: {sorted(stale_question_ids)[:15]}"
                )

            inserted = 0
            updated = 0

            for source_record in loop_questions:
                existing = managed_existing.get(
                    source_record["question_id"]
                )

                db_record = prepare_db_record(
                    source_record=source_record,
                    columns=columns,
                    existing=existing,
                )

                if existing:
                    await update_template(conn, db_record)
                    updated += 1
                else:
                    await insert_template(conn, db_record)
                    inserted += 1

            await validate_loaded_templates(
                conn=conn,
                expected_questions=loop_questions,
            )

        logger.info(
            "forms.card_templates population finished successfully. "
            f"Inserted: {inserted}. Updated: {updated}. "
            f"Expected/processed: {len(loop_questions)}."
        )

    except Exception as exc:
        logger.exception(
            f"Failed to populate forms.card_templates: {exc}"
        )
        raise
