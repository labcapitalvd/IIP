"""Puebla rules.field_rules para el Índice de Innovación Pública.

Dependencias previas:
    11c_seed_sections.py
    11d_seed_questions.py
    11e_seed_loop_questions.py
    11f_seed_card_templates.py
    11g_seed_field_groups.py
    11h_seed_fields.py

Alcance actual:
    - 2019
    - 2021
    - 2023

Reglas creadas:
    - MIN_VALUE = 0 para campos numéricos que representan cantidades,
      presupuestos, valores monetarios, decimales o porcentajes.
    - MAX_VALUE = 100 únicamente para campos cuyo Tipo_dato sea porcentaje.

Para el Excel activo no existen campos de tipo porcentaje, por lo que el
resultado esperado actual es:
    - 2019: 14 reglas MIN_VALUE
    - 2021: 16 reglas MIN_VALUE
    - 2023: 21 reglas MIN_VALUE
    - Total: 51 reglas

Decisiones de diseño:
    - No se crean reglas de longitud, expresiones regulares o máximos
      arbitrarios porque el instrumento no las documenta.
    - No se usa ni se modifica helper.
    - No se guardan ponderaciones Maxc, Maxv, Maxi, Maxp, Maxb o Valor_maximo.
    - Las relaciones se construyen exclusivamente con UUIDv7 y llaves foráneas.
    - Los registros existentes conservan su UUIDv7.
    - La idempotencia se basa en (field_id, rule_type_id).

Limitación conocida del modelo:
    - El catálogo actual no incluye una regla INTEGER_ONLY. Por ello, este
      poblador evita números negativos, pero no puede impedir valores decimales
      en campos de Tipo_dato entero. Esa validación requeriría agregar un nuevo
      RuleType y soporte en el motor de formularios.
"""

from __future__ import annotations

import asyncio
import importlib.util
from collections import OrderedDict, defaultdict
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from uuid_utils import uuid7

from shared.infrastructure import async_engine
from shared.utils.logger import get_logger


logger = get_logger(__name__)

ACTIVE_YEARS = (2019, 2021, 2023)

# Descripciones compatibles con shared.enums.RuleTypesEnum.
REQUIRED_RULE_TYPES = OrderedDict(
    {
        "MIN_VALUE": "min_value",
        "MAX_VALUE": "max_value",
    }
)

# Tipos de dato en los que un valor negativo no tiene sentido para el IIP.
NON_NEGATIVE_DATA_TYPES = {
    "entero",
    "monetario",
    "decimal",
    "porcentaje",
}

EXPECTED_RULE_COUNTS_BY_YEAR = {
    2019: 14,
    2021: 16,
    2023: 21,
}
EXPECTED_TOTAL = sum(EXPECTED_RULE_COUNTS_BY_YEAR.values())


# -----------------------------------------------------------------------------
# CARGA DE 11h: MISMA INTERPRETACIÓN DEL EXCEL Y DE LOS FIELDS
# -----------------------------------------------------------------------------


def load_fields_module():
    """Carga 11h para reutilizar exactamente su interpretación del Excel."""
    module_path = Path(__file__).with_name("11h_seed_fields.py")

    if not module_path.is_file():
        raise FileNotFoundError(
            "No se encontró 11h_seed_fields.py en la misma carpeta de 12b. "
            f"Ruta esperada: {module_path}"
        )

    spec = importlib.util.spec_from_file_location(
        "iip_seed_fields_for_rules",
        module_path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"No fue posible cargar el módulo de fields: {module_path}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_fields_module()


# -----------------------------------------------------------------------------
# UTILIDADES
# -----------------------------------------------------------------------------


def clean(value):
    return H.clean(value)


def normalize_token(value):
    return H.normalize_token(value)


def is_uuidv7(value) -> bool:
    try:
        return UUID(str(value)).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    return str(uuid7())


def truncate(value, max_length):
    return H.truncate(value, max_length)


def spec_key(spec: dict) -> tuple[int, str, str, int]:
    """Llave estable usada por 11h para relacionar una especificación y su field."""
    return (
        int(spec["year"]),
        spec["question_code"],
        spec["group_kind"],
        int(spec["display_order"]),
    )


# -----------------------------------------------------------------------------
# CONSTRUCCIÓN DE REGLAS ESPERADAS
# -----------------------------------------------------------------------------


def build_rule_blueprints(field_specs: list[dict]) -> list[dict]:
    """Construye únicamente reglas justificadas por el tipo de dato.

    Cada blueprint todavía no contiene UUID de PostgreSQL. Estos se resuelven
    posteriormente con el mapa de fields construido por 11h.
    """
    blueprints: list[dict] = []

    for spec in field_specs:
        data_type = normalize_token(spec["data_type"])

        if data_type not in NON_NEGATIVE_DATA_TYPES:
            continue

        if spec["field_type_label"] != "NUMERIC":
            raise ValueError(
                "Un Tipo_dato numérico fue mapeado a un field_type distinto "
                f"de NUMERIC: {spec_key(spec)}; "
                f"Tipo_dato={spec['data_type']!r}; "
                f"field_type={spec['field_type_label']!r}."
            )

        blueprints.append(
            {
                "field_key": spec_key(spec),
                "year": int(spec["year"]),
                "question_code": spec["question_code"],
                "group_kind": spec["group_kind"],
                "field_display_order": int(spec["display_order"]),
                "data_type": data_type,
                "rule_type": "MIN_VALUE",
                "rule_value": "0",
                "error_message": "El valor debe ser mayor o igual a 0.",
            }
        )

        # Se mantiene preparado para futuras versiones del instrumento.
        if data_type == "porcentaje":
            blueprints.append(
                {
                    "field_key": spec_key(spec),
                    "year": int(spec["year"]),
                    "question_code": spec["question_code"],
                    "group_kind": spec["group_kind"],
                    "field_display_order": int(spec["display_order"]),
                    "data_type": data_type,
                    "rule_type": "MAX_VALUE",
                    "rule_value": "100",
                    "error_message": "El porcentaje debe ser menor o igual a 100.",
                }
            )

    natural_keys = [
        (blueprint["field_key"], blueprint["rule_type"])
        for blueprint in blueprints
    ]
    if len(natural_keys) != len(set(natural_keys)):
        raise ValueError(
            "La construcción de field_rules produjo llaves duplicadas."
        )

    counts_by_year: dict[int, int] = defaultdict(int)
    counts_by_rule: dict[str, int] = defaultdict(int)

    for blueprint in blueprints:
        counts_by_year[blueprint["year"]] += 1
        counts_by_rule[blueprint["rule_type"]] += 1

    if dict(counts_by_year) != EXPECTED_RULE_COUNTS_BY_YEAR:
        raise ValueError(
            "Conteos inesperados de reglas por año. "
            f"Esperado={EXPECTED_RULE_COUNTS_BY_YEAR}; "
            f"obtenido={dict(counts_by_year)}."
        )

    if len(blueprints) != EXPECTED_TOTAL:
        raise ValueError(
            f"Se esperaban {EXPECTED_TOTAL} field_rules y se construyeron "
            f"{len(blueprints)}."
        )

    if counts_by_rule != {"MIN_VALUE": EXPECTED_TOTAL}:
        raise ValueError(
            "El Excel activo debería producir únicamente reglas MIN_VALUE. "
            f"Obtenido={dict(counts_by_rule)}."
        )

    return blueprints


# -----------------------------------------------------------------------------
# METADATOS Y CATÁLOGOS DE POSTGRESQL
# -----------------------------------------------------------------------------


async def get_table_columns(conn, schema: str, table: str) -> dict:
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
            ORDER BY ordinal_position;
            """
        ),
        {"schema": schema, "table": table},
    )

    rows = result.mappings().all()
    if not rows:
        raise ValueError(f"No existe la tabla {schema}.{table}.")

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_field_rules_columns(columns: dict) -> None:
    required = {
        "id",
        "field_id",
        "rule_type_id",
        "rule_value",
        "error_message",
        "updated_at",
    }
    missing = required - set(columns)
    if missing:
        raise ValueError(
            "La tabla rules.field_rules no tiene todas las columnas "
            f"requeridas. Faltan: {sorted(missing)}"
        )


async def ensure_rule_types(conn) -> dict[str, str]:
    """Obtiene o crea MIN_VALUE y MAX_VALUE usando UUIDv7."""
    result = await conn.execute(
        text(
            """
            SELECT UPPER(TRIM(label)) AS label, id::text AS id
            FROM reference.rule_types
            ORDER BY label, id;
            """
        )
    )

    grouped: dict[str, list[str]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[row["label"]].append(row["id"])

    for label, ids in grouped.items():
        if len(ids) > 1:
            raise ValueError(
                f"Existen rule_types duplicados para {label}: {ids}"
            )

    for label, description in REQUIRED_RULE_TYPES.items():
        existing = grouped.get(label, [])

        if existing:
            if not is_uuidv7(existing[0]):
                raise ValueError(
                    f"El rule_type {label} no tiene UUIDv7: {existing[0]}"
                )
            continue

        rule_type_id = new_uuidv7()
        await conn.execute(
            text(
                """
                INSERT INTO reference.rule_types (
                    id,
                    label,
                    description
                )
                VALUES (
                    CAST(:id AS uuid),
                    :label,
                    :description
                );
                """
            ),
            {
                "id": rule_type_id,
                "label": label,
                "description": description,
            },
        )
        grouped[label] = [rule_type_id]
        logger.info(f"Created reference.rule_types: {label}")

    return {
        label: grouped[label][0]
        for label in REQUIRED_RULE_TYPES
    }


# -----------------------------------------------------------------------------
# RESOLUCIÓN DE FIELDS Y REGLAS EXISTENTES
# -----------------------------------------------------------------------------


async def resolve_field_map(
    conn,
    main_questions,
    loops,
    field_specs: list[dict],
) -> dict[tuple[int, str, str, int], dict]:
    """Relaciona cada especificación del Excel con su field UUIDv7 real."""
    questions = await H.get_questions(
        conn=conn,
        main_questions=main_questions,
        loops=loops,
    )

    direct_groups, card_groups = await H.get_groups(
        conn=conn,
        questions=questions,
        main_questions=main_questions,
        loops=loops,
    )

    field_map = await H.get_field_map_for_specs(
        conn=conn,
        specs=field_specs,
        direct_groups=direct_groups,
        card_groups=card_groups,
    )

    for key, field in field_map.items():
        if not is_uuidv7(field["field_id"]):
            raise ValueError(
                f"El field resuelto para {key} no tiene UUIDv7: "
                f"{field['field_id']}"
            )

    return field_map


async def get_existing_rules(conn) -> dict[tuple[str, str], dict]:
    """Obtiene reglas existentes por (field_id, rule_type_label)."""
    result = await conn.execute(
        text(
            """
            SELECT
                field_rule.id::text AS field_rule_id,
                field_rule.field_id::text AS field_id,
                field_rule.rule_type_id::text AS rule_type_id,
                UPPER(TRIM(rule_type.label)) AS rule_type_label,
                field_rule.rule_value,
                field_rule.error_message
            FROM rules.field_rules field_rule
            JOIN reference.rule_types rule_type
              ON rule_type.id = field_rule.rule_type_id
            ORDER BY field_rule.field_id, rule_type.label, field_rule.id;
            """
        )
    )

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[
            (row["field_id"], row["rule_type_label"])
        ].append(dict(row))

    lookup: dict[tuple[str, str], dict] = {}
    for key, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                f"Existen field_rules duplicadas para {key}: "
                f"{[row['field_rule_id'] for row in rows]}"
            )

        if not is_uuidv7(rows[0]["field_rule_id"]):
            raise ValueError(
                "La field_rule existente no tiene UUIDv7: "
                f"{rows[0]['field_rule_id']}"
            )

        lookup[key] = rows[0]

    return lookup


# -----------------------------------------------------------------------------
# INSERCIÓN Y ACTUALIZACIÓN
# -----------------------------------------------------------------------------


async def save_rule(conn, record: dict, update: bool) -> None:
    if update:
        statement = text(
            """
            UPDATE rules.field_rules
            SET
                field_id = CAST(:field_id AS uuid),
                rule_type_id = CAST(:rule_type_id AS uuid),
                rule_value = :rule_value,
                error_message = :error_message,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
            """
        )
    else:
        statement = text(
            """
            INSERT INTO rules.field_rules (
                id,
                field_id,
                rule_type_id,
                rule_value,
                error_message,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:field_id AS uuid),
                CAST(:rule_type_id AS uuid),
                :rule_value,
                :error_message,
                NOW()
            );
            """
        )

    await conn.execute(statement, record)


async def persist_rules(
    conn,
    blueprints: list[dict],
    field_map: dict[tuple[int, str, str, int], dict],
    rule_types: dict[str, str],
    columns: dict,
) -> tuple[int, int, list[dict]]:
    existing = await get_existing_rules(conn)

    inserted = 0
    updated = 0
    expected_records: list[dict] = []

    for blueprint in blueprints:
        field = field_map.get(blueprint["field_key"])
        if field is None:
            raise ValueError(
                "No se encontró el field esperado para la regla: "
                f"{blueprint['field_key']}"
            )

        if field["field_type_label"] != "NUMERIC":
            raise ValueError(
                "La regla numérica apunta a un field no NUMERIC: "
                f"{blueprint['field_key']}; "
                f"tipo={field['field_type_label']}."
            )

        field_id = field["field_id"]
        rule_type_label = blueprint["rule_type"]
        rule_type_id = rule_types[rule_type_label]
        natural_key = (field_id, rule_type_label)
        old = existing.get(natural_key)

        field_rule_id = (
            old["field_rule_id"]
            if old is not None
            else new_uuidv7()
        )

        if not is_uuidv7(field_rule_id):
            raise ValueError(
                f"El ID preparado para field_rule no es UUIDv7: {field_rule_id}"
            )

        rule_value = truncate(
            blueprint["rule_value"],
            columns["rule_value"]["max_length"],
        )
        error_message = truncate(
            blueprint["error_message"],
            columns["error_message"]["max_length"],
        )

        if rule_value is None:
            raise ValueError(
                f"rule_value vacío para {blueprint['field_key']}"
            )
        if error_message is None:
            raise ValueError(
                f"error_message vacío para {blueprint['field_key']}"
            )

        record = {
            "id": field_rule_id,
            "field_id": field_id,
            "rule_type_id": rule_type_id,
            "rule_value": rule_value,
            "error_message": error_message,
            "year": blueprint["year"],
            "rule_type_label": rule_type_label,
        }

        await save_rule(
            conn=conn,
            record=record,
            update=old is not None,
        )

        if old is None:
            inserted += 1
        else:
            updated += 1

        expected_records.append(record)

    return inserted, updated, expected_records


# -----------------------------------------------------------------------------
# VALIDACIÓN POSTERIOR
# -----------------------------------------------------------------------------


async def validate_loaded_rules(
    conn,
    expected_records: list[dict],
) -> None:
    expected_by_key = {
        (record["field_id"], record["rule_type_label"]): record
        for record in expected_records
    }

    result = await conn.execute(
        text(
            """
            SELECT
                field_rule.id::text AS field_rule_id,
                field_rule.field_id::text AS field_id,
                field_rule.rule_value,
                field_rule.error_message,
                UPPER(TRIM(rule_type.label)) AS rule_type_label,
                UPPER(TRIM(field_type.label)) AS field_type_label,
                form.anno
            FROM rules.field_rules field_rule
            JOIN reference.rule_types rule_type
              ON rule_type.id = field_rule.rule_type_id
            JOIN forms.fields field
              ON field.id = field_rule.field_id
            JOIN reference.field_types field_type
              ON field_type.id = field.field_type_id
            JOIN forms.forms form
              ON form.id = field.form_id
            WHERE form.anno IN (2019, 2021, 2023)
            ORDER BY form.anno, field_rule.field_id, rule_type.label;
            """
        )
    )

    loaded: dict[tuple[str, str], dict] = {}

    for row in result.mappings().all():
        key = (row["field_id"], row["rule_type_label"])

        if key not in expected_by_key:
            # No se intervienen reglas adicionales creadas por otras funciones.
            continue

        if key in loaded:
            raise ValueError(
                f"La field_rule esperada {key} aparece más de una vez."
            )

        loaded[key] = dict(row)

    missing = set(expected_by_key) - set(loaded)
    if missing:
        raise ValueError(
            "No se cargaron todas las field_rules esperadas. "
            f"Faltan: {list(missing)[:20]}"
        )

    counts_by_year: dict[int, int] = defaultdict(int)

    for key, expected in expected_by_key.items():
        row = loaded[key]

        if not is_uuidv7(row["field_rule_id"]):
            raise ValueError(
                f"La field_rule {key} no tiene UUIDv7: "
                f"{row['field_rule_id']}"
            )

        if row["field_type_label"] != "NUMERIC":
            raise ValueError(
                f"La field_rule {key} apunta a un field no NUMERIC."
            )

        if clean(row["rule_value"]) != clean(expected["rule_value"]):
            raise ValueError(
                f"rule_value incorrecto para {key}. "
                f"SQL={row['rule_value']!r}; "
                f"esperado={expected['rule_value']!r}."
            )

        if clean(row["error_message"]) != clean(expected["error_message"]):
            raise ValueError(
                f"error_message incorrecto para {key}."
            )

        counts_by_year[int(row["anno"])] += 1

    if dict(counts_by_year) != EXPECTED_RULE_COUNTS_BY_YEAR:
        raise ValueError(
            "Validación de field_rules por año falló. "
            f"Esperado={EXPECTED_RULE_COUNTS_BY_YEAR}; "
            f"obtenido={dict(counts_by_year)}."
        )

    logger.info(
        "rules.field_rules validation passed successfully. "
        f"Validated rules: {len(expected_by_key)}."
    )


# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    """Puebla las reglas mínimas y máximas justificadas por el instrumento."""

    path = Path(H.FILE_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    logger.info(f"Starting rules.field_rules population from {path}")
    print(f"[12b] Archivo Excel: {path}", flush=True)

    main_questions, loops, _responses, field_specs = H.load_instrument(path)
    blueprints = build_rule_blueprints(field_specs)

    print(
        "[12b] Reglas construidas: "
        "2019=14, 2021=16, 2023=21, total=51.",
        flush=True,
    )

    async with async_engine.begin() as conn:
        columns = await get_table_columns(
            conn=conn,
            schema="rules",
            table="field_rules",
        )
        validate_field_rules_columns(columns)

        rule_types = await ensure_rule_types(conn)

        field_map = await resolve_field_map(
            conn=conn,
            main_questions=main_questions,
            loops=loops,
            field_specs=field_specs,
        )

        inserted, updated, expected_records = await persist_rules(
            conn=conn,
            blueprints=blueprints,
            field_map=field_map,
            rule_types=rule_types,
            columns=columns,
        )

        await validate_loaded_rules(
            conn=conn,
            expected_records=expected_records,
        )

    logger.info(
        "rules.field_rules population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}. Total: {EXPECTED_TOTAL}."
    )
    print(
        f"[12b] OK. Insertados={inserted}; actualizados={updated}; "
        f"total={EXPECTED_TOTAL}.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
