"""Puebla forms.field_groups para el IIP 2019, 2021 y 2023.

Dependencias previas:
    11d_seed_questions.py
    11e_seed_loop_questions.py
    11f_seed_card_templates.py

Modelo:
    forms.field_groups.form_id
        -> forms.forms.id

    forms.field_groups.question_id
        -> forms.questions.id

    forms.field_groups.card_template_id
        -> forms.card_templates.id (nullable)

Estrategia:
- Se crea un grupo DIRECTO para cada pregunta principal que tiene respuesta
  directa. Su card_template_id queda en NULL.
- Se crea un grupo CARD para cada card_template administrado. Su
  card_template_id apunta a la plantilla repetible.
- La pregunta mixta Pregunta 28.1 recibe dos grupos:
    1. DIRECTO: para la respuesta Sí/No.
    2. CARD: para las subpreguntas repetibles.
- Los bucles independientes reciben únicamente el grupo CARD.
- forms.field_groups no tiene columna helper. Por eso la llave natural para
  idempotencia se basa en las relaciones:
    DIRECTO -> (question_id, card_template_id IS NULL)
    CARD    -> (question_id, card_template_id)
- Los registros nuevos usan UUID versión 7.
- Los registros existentes conservan su UUIDv7 y se actualizan.
- No se eliminan grupos antiguos automáticamente para evitar romper fields o
  respuestas existentes.
"""

import json
import os
from collections import defaultdict
from uuid import UUID

from sqlalchemy import text
from uuid_utils import uuid7

from shared_db import async_engine
from shared_utils.logger import get_logger


logger = get_logger("pop/field_groups")


# ---------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------

DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023)

VALID_SOURCES = {
    "Estructura IIP.xlsx",
    "Estructura_IIP.xlsx",
}

DIRECT_GROUP_KIND = "DIRECT"
CARD_GROUP_KIND = "CARD"


# ---------------------------------------------------------------------
# FUNCIONES GENERALES
# ---------------------------------------------------------------------


def get_active_years() -> tuple[int, ...]:
    """Obtiene los años activos desde IIP_ACTIVE_YEARS.

    Ejemplo:
        IIP_ACTIVE_YEARS=2019,2021,2023
    """
    raw_value = os.getenv("IIP_ACTIVE_YEARS")

    if not raw_value:
        return DEFAULT_ACTIVE_YEARS

    years = []

    for raw_year in raw_value.split(","):
        raw_year = raw_year.strip()

        if not raw_year:
            continue

        try:
            years.append(int(raw_year))
        except ValueError as exc:
            raise ValueError(
                "IIP_ACTIVE_YEARS debe contener años separados por coma. "
                f"Valor inválido: {raw_year!r}"
            ) from exc

    if not years:
        raise ValueError("IIP_ACTIVE_YEARS no contiene años válidos.")

    if len(years) != len(set(years)):
        raise ValueError(
            f"IIP_ACTIVE_YEARS contiene años repetidos: {years}"
        )

    return tuple(years)


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
    """Genera un UUID versión 7."""
    return str(uuid7())


def truncate(value, max_length):
    """Recorta texto cuando la columna tiene longitud máxima."""
    value = clean(value)

    if value is None or max_length is None:
        return value

    return value[:max_length]


def is_managed_question_helper(helper: dict | None) -> bool:
    """Valida que la pregunta pertenezca al poblado del IIP."""
    if not helper:
        return False

    return (
        helper.get("entity") == "forms.questions"
        and helper.get("source") in VALID_SOURCES
    )


def is_managed_card_helper(helper: dict | None) -> bool:
    """Valida que la plantilla pertenezca al poblado del IIP."""
    if not helper:
        return False

    return (
        helper.get("entity") == "forms.card_templates"
        and helper.get("source") in VALID_SOURCES
    )


def direct_response_exists(helper: dict) -> bool:
    """Determina si debe existir un grupo directo.

    Toda pregunta principal necesita un field_group directo, incluso cuando
    Respuestas_2023 representa su contenido mediante varias filas con
    Texto_subpregunta. Esas filas siguen siendo campos directos de la pregunta
    y no una tarjeta repetible.

    Los bucles independientes tienen is_main_question=False y, por tanto, no
    reciben grupo directo. La Pregunta 28.1 tiene is_main_question=True y
    is_loop=True, por lo que recibe tanto grupo DIRECT como grupo CARD.
    """
    return helper.get("is_main_question") is True


# ---------------------------------------------------------------------
# METADATOS DE POSTGRESQL
# ---------------------------------------------------------------------


async def get_table_columns(conn) -> dict:
    """Consulta la estructura real de forms.field_groups."""
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
              AND table_name = 'field_groups'
            ORDER BY ordinal_position;
            """
        )
    )

    rows = result.mappings().all()

    if not rows:
        raise ValueError(
            "No se encontró la tabla forms.field_groups en PostgreSQL."
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
    """Valida las columnas requeridas por el modelo."""
    required = {
        "id",
        "form_id",
        "question_id",
        "card_template_id",
        "label",
        "description",
        "display_order",
        "updated_at",
    }

    missing = required - set(columns)

    if missing:
        raise ValueError(
            "La tabla forms.field_groups no tiene todas las columnas "
            f"requeridas. Faltan: {sorted(missing)}"
        )

    if not columns["card_template_id"]["nullable"]:
        raise ValueError(
            "forms.field_groups.card_template_id debe permitir NULL para "
            "representar los grupos de respuesta directa."
        )


# ---------------------------------------------------------------------
# PREGUNTAS PRINCIPALES Y PLANTILLAS
# ---------------------------------------------------------------------


async def get_managed_questions(
    conn,
    active_years: tuple[int, ...],
) -> dict[str, dict]:
    """Obtiene preguntas administradas del IIP.

    Retorna:
        question_id -> datos de la pregunta
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
                q.display_order,
                q.required,
                q.is_loop,
                f.anno
            FROM forms.questions q
            JOIN forms.forms f
                ON f.id = q.form_id
            ORDER BY f.anno, q.display_order, q.id;
            """
        )
    )

    questions = {}

    for row in result.mappings().all():
        if int(row["anno"]) not in active_years:
            continue

        helper = parse_helper(row["helper"])

        if not is_managed_question_helper(helper):
            continue

        question_id = row["question_id"]
        form_id = row["form_id"]

        if not is_uuidv7(question_id):
            raise ValueError(
                f"La pregunta administrada no tiene UUIDv7: {question_id}"
            )

        if not is_uuidv7(form_id):
            raise ValueError(
                f"El form_id de la pregunta {question_id} no es UUIDv7."
            )

        helper_year = helper.get("year")
        database_year = int(row["anno"])

        if helper_year is not None and int(helper_year) != database_year:
            raise ValueError(
                f"La pregunta {question_id} pertenece al formulario "
                f"{database_year}, pero su helper indica {helper_year}."
            )

        if question_id in questions:
            raise ValueError(
                f"La pregunta {question_id} aparece más de una vez."
            )

        questions[question_id] = {
            "question_id": question_id,
            "form_id": form_id,
            "section_id": row["section_id"],
            "year": database_year,
            "label": row["label"],
            "description": row["description"],
            "question_display_order": int(row["display_order"] or 0),
            "required": row["required"],
            "is_loop": row["is_loop"],
            "helper": helper,
            "is_main_question": helper.get("is_main_question") is True,
            "is_mixed_question": helper.get("is_mixed_question") is True,
            "question_code": clean(helper.get("question_code")),
            "question_raw_code": clean(
                helper.get("question_raw_code") or row["label"]
            ),
            "indicator_code": clean(helper.get("indicator_code")),
        }

    if not questions:
        raise ValueError(
            "No se encontraron preguntas administradas. Ejecuta antes "
            "11d_seed_questions.py y 11e_seed_loop_questions.py."
        )

    return questions


async def get_managed_card_templates(
    conn,
    questions: dict[str, dict],
) -> dict[str, dict]:
    """Obtiene card_templates administrados.

    Retorna:
        card_template_id -> datos de la plantilla
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
                q.is_loop,
                f.anno
            FROM forms.card_templates ct
            JOIN forms.questions q
                ON q.id = ct.question_id
            JOIN forms.forms f
                ON f.id = q.form_id
            WHERE f.anno = 2023
            ORDER BY ct.question_id, ct.id;
            """
        )
    )

    templates = {}
    templates_by_question = defaultdict(list)

    for row in result.mappings().all():
        helper = parse_helper(row["helper"])

        if not is_managed_card_helper(helper):
            continue

        card_template_id = row["card_template_id"]
        question_id = row["question_id"]

        if question_id not in questions:
            raise ValueError(
                "La plantilla administrada apunta a una pregunta que no fue "
                f"reconocida como parte del IIP: {question_id}."
            )

        if not is_uuidv7(card_template_id):
            raise ValueError(
                f"El card_template no tiene UUIDv7: {card_template_id}"
            )

        if row["is_loop"] is not True:
            raise ValueError(
                f"El card_template {card_template_id} apunta a una pregunta "
                "con is_loop distinto de TRUE."
            )

        helper_question_id = clean(helper.get("question_id"))

        if (
            helper_question_id is not None
            and helper_question_id != question_id
        ):
            raise ValueError(
                f"El helper de {card_template_id} indica question_id "
                f"{helper_question_id}, pero la FK apunta a {question_id}."
            )

        templates_by_question[question_id].append(card_template_id)

        templates[card_template_id] = {
            "card_template_id": card_template_id,
            "question_id": question_id,
            "year": int(row["anno"]),
            "label": row["label"],
            "description": row["description"],
            "helper": helper,
        }

    duplicated = {
        question_id: ids
        for question_id, ids in templates_by_question.items()
        if len(ids) > 1
    }

    if duplicated:
        raise ValueError(
            "Se encontró más de un card_template administrado para algunas "
            f"preguntas: {duplicated}"
        )

    loop_question_ids = {
        question_id
        for question_id, question in questions.items()
        if question["year"] == 2023
        and question["is_loop"] is True
    }

    template_question_ids = set(templates_by_question)
    missing_templates = loop_question_ids - template_question_ids

    if missing_templates:
        sample = [
            questions[question_id]["question_raw_code"]
            for question_id in sorted(missing_templates)[:15]
        ]
        raise ValueError(
            "Existen preguntas tipo bucle sin card_template. Ejecuta antes "
            "11f_seed_card_templates.py. "
            f"Total: {len(missing_templates)}. Muestra: {sample}"
        )

    return templates


# ---------------------------------------------------------------------
# CONSTRUCCIÓN DE GRUPOS ESPERADOS
# ---------------------------------------------------------------------


def build_expected_groups(
    questions: dict[str, dict],
    templates: dict[str, dict],
) -> list[dict]:
    """Construye grupos directos y grupos asociados a tarjetas."""
    records = []

    # Un grupo directo por pregunta principal con respuesta directa.
    for question in questions.values():
        helper = question["helper"]

        if not question["is_main_question"]:
            continue

        if not direct_response_exists(helper):
            continue

        records.append(
            {
                "group_kind": DIRECT_GROUP_KIND,
                "natural_key": (
                    question["question_id"],
                    None,
                ),
                "form_id": question["form_id"],
                "question_id": question["question_id"],
                "card_template_id": None,
                "year": question["year"],
                "question_label": question["label"],
                "question_description": question["description"],
                "question_code": question["question_code"],
                "question_raw_code": question["question_raw_code"],
                "is_main_question": True,
                "is_mixed_question": question["is_mixed_question"],
                "display_order": 1,
            }
        )

    # Un grupo de tarjeta por cada plantilla administrada.
    for template in templates.values():
        question = questions[template["question_id"]]

        records.append(
            {
                "group_kind": CARD_GROUP_KIND,
                "natural_key": (
                    question["question_id"],
                    template["card_template_id"],
                ),
                "form_id": question["form_id"],
                "question_id": question["question_id"],
                "card_template_id": template["card_template_id"],
                "year": question["year"],
                "question_label": question["label"],
                "question_description": question["description"],
                "question_code": question["question_code"],
                "question_raw_code": question["question_raw_code"],
                "card_template_label": template["label"],
                "card_template_description": template["description"],
                "is_main_question": question["is_main_question"],
                "is_mixed_question": question["is_mixed_question"],
                # En una pregunta mixta, primero aparece la respuesta directa
                # y después la tarjeta repetible.
                "display_order": (
                    2 if question["is_mixed_question"] else 1
                ),
            }
        )

    records.sort(
        key=lambda record: (
            int(record["year"]),
            questions[record["question_id"]]["question_display_order"],
            int(record["display_order"]),
            record["group_kind"],
        )
    )

    keys = [record["natural_key"] for record in records]

    if len(keys) != len(set(keys)):
        raise ValueError(
            "La construcción de field_groups produjo llaves duplicadas."
        )

    direct_count = sum(
        1 for record in records
        if record["group_kind"] == DIRECT_GROUP_KIND
    )
    card_count = sum(
        1 for record in records
        if record["group_kind"] == CARD_GROUP_KIND
    )
    mixed_group_count = sum(
        1 for record in records
        if record["is_mixed_question"]
    )

    logger.info(
        "Expected field groups: "
        f"direct={direct_count}, card={card_count}, total={len(records)}, "
        f"groups belonging to mixed questions={mixed_group_count}."
    )

    return records


# ---------------------------------------------------------------------
# GRUPOS EXISTENTES
# ---------------------------------------------------------------------


async def get_existing_groups(
    conn,
    target_question_ids: set[str],
) -> dict[tuple[str, str | None], dict]:
    """Obtiene field_groups existentes para las preguntas objetivo.

    Como forms.field_groups no tiene helper, la llave natural es:
        (question_id, card_template_id)
    """
    if not target_question_ids:
        return {}

    result = await conn.execute(
        text(
            """
            SELECT
                fg.id::text AS field_group_id,
                fg.form_id::text AS form_id,
                fg.question_id::text AS question_id,
                fg.card_template_id::text AS card_template_id,
                fg.label,
                fg.description,
                fg.display_order,

                q.form_id::text AS question_form_id,

                ct.question_id::text AS template_question_id

            FROM forms.field_groups fg

            JOIN forms.questions q
                ON q.id = fg.question_id

            LEFT JOIN forms.card_templates ct
                ON ct.id = fg.card_template_id

            ORDER BY fg.question_id, fg.card_template_id, fg.id;
            """
        )
    )

    existing = {}

    for row in result.mappings().all():
        if row["question_id"] not in target_question_ids:
            continue

        field_group_id = row["field_group_id"]
        question_id = row["question_id"]
        card_template_id = row["card_template_id"]

        if not is_uuidv7(field_group_id):
            raise ValueError(
                f"El field_group existente no tiene UUIDv7: {field_group_id}"
            )

        if row["form_id"] != row["question_form_id"]:
            raise ValueError(
                f"El field_group {field_group_id} y su pregunta pertenecen "
                "a formularios diferentes."
            )

        if card_template_id is not None:
            if row["template_question_id"] is None:
                raise ValueError(
                    f"El field_group {field_group_id} apunta a un "
                    "card_template inexistente."
                )

            if row["template_question_id"] != question_id:
                raise ValueError(
                    f"El field_group {field_group_id} relaciona la pregunta "
                    f"{question_id} con una plantilla perteneciente a "
                    f"{row['template_question_id']}."
                )

        key = (
            question_id,
            card_template_id,
        )

        if key in existing:
            raise ValueError(
                "Existen field_groups duplicados para la llave "
                f"{key}: {existing[key]['field_group_id']} y "
                f"{field_group_id}."
            )

        existing[key] = dict(row)

    return existing


# ---------------------------------------------------------------------
# PREPARACIÓN E INSERCIÓN
# ---------------------------------------------------------------------


def make_label(record: dict) -> str:
    """Construye un label legible para el grupo."""
    raw_code = (
        clean(record["question_raw_code"])
        or clean(record["question_label"])
        or record["question_code"]
    )

    if record["group_kind"] == DIRECT_GROUP_KIND:
        return f"Respuesta - {raw_code}"

    return f"Detalle repetible - {raw_code}"


def make_description(record: dict) -> str:
    """Construye la descripción del grupo."""
    if record["group_kind"] == DIRECT_GROUP_KIND:
        question_text = clean(record["question_description"])

        return (
            f"Campos de respuesta directa para {record['question_raw_code']}. "
            f"{question_text or ''}"
        ).strip()

    card_description = clean(record.get("card_template_description"))
    question_text = clean(record["question_description"])

    return (
        card_description
        or question_text
        or f"Campos repetibles para {record['question_raw_code']}."
    )


def prepare_db_record(
    source_record: dict,
    columns: dict,
    existing: dict | None,
) -> dict:
    """Prepara INSERT o UPDATE de forms.field_groups."""
    field_group_id = (
        existing["field_group_id"]
        if existing
        else new_uuidv7()
    )

    if not is_uuidv7(field_group_id):
        raise ValueError(
            f"El ID preparado para field_group no es UUIDv7: "
            f"{field_group_id}"
        )

    full_label = make_label(source_record)
    label = truncate(
        full_label,
        columns["label"]["max_length"],
    )

    if label is None:
        raise ValueError(
            f"No fue posible construir label para {source_record['natural_key']}."
        )

    description = truncate(
        make_description(source_record),
        columns["description"]["max_length"],
    )

    if description is None and not columns["description"]["nullable"]:
        description = label

    return {
        "id": field_group_id,
        "form_id": source_record["form_id"],
        "question_id": source_record["question_id"],
        "card_template_id": source_record["card_template_id"],
        "label": label,
        "description": description,
        "display_order": int(source_record["display_order"]),
    }


async def insert_group(conn, record: dict) -> None:
    """Inserta un field_group nuevo."""
    await conn.execute(
        text(
            """
            INSERT INTO forms.field_groups (
                id,
                form_id,
                question_id,
                card_template_id,
                label,
                description,
                display_order,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:form_id AS uuid),
                CAST(:question_id AS uuid),
                CAST(:card_template_id AS uuid),
                :label,
                :description,
                :display_order,
                NOW()
            );
            """
        ),
        record,
    )


async def update_group(conn, record: dict) -> None:
    """Actualiza un field_group conservando su UUID."""
    await conn.execute(
        text(
            """
            UPDATE forms.field_groups
            SET
                form_id = CAST(:form_id AS uuid),
                question_id = CAST(:question_id AS uuid),
                card_template_id = CAST(:card_template_id AS uuid),
                label = :label,
                description = :description,
                display_order = :display_order,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
            """
        ),
        record,
    )


# ---------------------------------------------------------------------
# VALIDACIÓN POSTERIOR
# ---------------------------------------------------------------------


async def validate_loaded_groups(
    conn,
    expected_records: list[dict],
) -> None:
    """Valida las relaciones y UUID de los grupos esperados."""
    expected_by_key = {
        record["natural_key"]: record
        for record in expected_records
    }

    question_ids = {
        record["question_id"]
        for record in expected_records
    }

    result = await conn.execute(
        text(
            """
            SELECT
                fg.id::text AS field_group_id,
                fg.form_id::text AS form_id,
                fg.question_id::text AS question_id,
                fg.card_template_id::text AS card_template_id,
                fg.display_order,

                q.form_id::text AS question_form_id,

                ct.id::text AS real_card_template_id,
                ct.question_id::text AS template_question_id

            FROM forms.field_groups fg

            JOIN forms.questions q
                ON q.id = fg.question_id

            LEFT JOIN forms.card_templates ct
                ON ct.id = fg.card_template_id

            ORDER BY fg.question_id, fg.card_template_id, fg.id;
            """
        )
    )

    loaded = {}

    for row in result.mappings().all():
        if row["question_id"] not in question_ids:
            continue

        key = (
            row["question_id"],
            row["card_template_id"],
        )

        if key not in expected_by_key:
            continue

        if key in loaded:
            raise ValueError(
                f"El field_group esperado {key} aparece más de una vez."
            )

        loaded[key] = row

    missing_keys = set(expected_by_key) - set(loaded)

    if missing_keys:
        raise ValueError(
            "No se cargaron todos los field_groups esperados. "
            f"Faltan: {list(missing_keys)[:20]}"
        )

    for key, expected in expected_by_key.items():
        row = loaded[key]

        if not is_uuidv7(row["field_group_id"]):
            raise ValueError(
                f"El field_group {key} no tiene UUIDv7: "
                f"{row['field_group_id']}"
            )

        if row["form_id"] != row["question_form_id"]:
            raise ValueError(
                f"El field_group {key} y su pregunta pertenecen a "
                "formularios diferentes."
            )

        if row["form_id"] != expected["form_id"]:
            raise ValueError(
                f"El field_group {key} quedó asociado al form_id incorrecto."
            )

        if int(row["display_order"]) != int(expected["display_order"]):
            raise ValueError(
                f"El field_group {key} tiene display_order "
                f"{row['display_order']}, pero se esperaba "
                f"{expected['display_order']}."
            )

        if expected["group_kind"] == DIRECT_GROUP_KIND:
            if row["card_template_id"] is not None:
                raise ValueError(
                    f"El grupo directo {key} no debe tener card_template_id."
                )
        else:
            if row["real_card_template_id"] is None:
                raise ValueError(
                    f"El grupo CARD {key} apunta a una plantilla inexistente."
                )

            if row["template_question_id"] != row["question_id"]:
                raise ValueError(
                    f"El grupo CARD {key} utiliza una plantilla de otra pregunta."
                )

    logger.info(
        "forms.field_groups validation passed successfully. "
        f"Validated groups: {len(expected_by_key)}."
    )


# ---------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------------------------------------------------


async def upgrade(gh, api) -> None:
    """Carga forms.field_groups."""
    del gh
    del api

    active_years = get_active_years()

    logger.info(
        "Starting forms.field_groups population. "
        f"Active years: {active_years}."
    )

    try:
        async with async_engine.begin() as conn:
            columns = await get_table_columns(conn)
            validate_required_columns(columns)

            questions = await get_managed_questions(
                conn=conn,
                active_years=active_years,
            )

            templates = await get_managed_card_templates(
                conn=conn,
                questions=questions,
            )

            expected_records = build_expected_groups(
                questions=questions,
                templates=templates,
            )

            target_question_ids = {
                record["question_id"]
                for record in expected_records
            }

            existing_groups = await get_existing_groups(
                conn=conn,
                target_question_ids=target_question_ids,
            )

            expected_keys = {
                record["natural_key"]
                for record in expected_records
            }

            stale_keys = set(existing_groups) - expected_keys

            if stale_keys:
                logger.warning(
                    "Existen field_groups para preguntas administradas que no "
                    "corresponden a la estructura esperada actual. No se "
                    "eliminan automáticamente para evitar romper fields o "
                    "respuestas. "
                    f"Total: {len(stale_keys)}. "
                    f"Muestra: {list(stale_keys)[:15]}"
                )

            inserted = 0
            updated = 0

            for source_record in expected_records:
                key = source_record["natural_key"]
                existing = existing_groups.get(key)

                db_record = prepare_db_record(
                    source_record=source_record,
                    columns=columns,
                    existing=existing,
                )

                if existing:
                    await update_group(
                        conn=conn,
                        record=db_record,
                    )
                    updated += 1
                else:
                    await insert_group(
                        conn=conn,
                        record=db_record,
                    )
                    inserted += 1

            await validate_loaded_groups(
                conn=conn,
                expected_records=expected_records,
            )

        logger.info(
            "forms.field_groups population finished successfully. "
            f"Inserted: {inserted}. Updated: {updated}. "
            f"Total expected: {len(expected_records)}."
        )

    except Exception as exc:
        logger.exception(
            f"Failed to run forms.field_groups population: {exc}"
        )
        raise
