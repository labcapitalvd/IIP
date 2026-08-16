"""Puebla rules.field_dependencies para el IIP.

Dependencias previas:
    11c_seed_sections.py
    11d_seed_questions.py
    11e_seed_loop_questions.py
    11f_seed_card_templates.py
    11g_seed_field_groups.py
    11h_seed_fields.py
    11i_seed_field_choices.py

Alcance actual:
    - IIP 2021: flujo condicional de Preguntas 21 a 23.
    - IIP 2023: activación de los 27 grupos repetibles.
    - IIP 2019: no se crean dependencias porque el Excel no documenta una
      condición explícita que pueda modelarse sin inventar reglas.

Convención:
    - Los registros nuevos usan UUID versión 7.
    - Las relaciones se construyen exclusivamente con llaves foráneas UUIDv7.
    - No se usa ni se modifica ninguna columna helper.
    - No se guardan ponderaciones Max ni metadatos técnicos.
    - rules.field_dependencies no tiene label ni description.

Formato de expected_value:
    EQUAL BOOLEAN:
        {"value": true}

    GREATER_THAN NUMERIC:
        {"value": 0}

    CONTAINS MULTI_CHOICE:
        {"choice_id": "<UUIDv7 de forms.field_choices>"}

El script crea en reference.relational_operators los operadores requeridos si
no existen. CONTAINS es necesario para evaluar selecciones múltiples.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any
from uuid import UUID

from shared.infrastructure import async_engine
from shared.utils.logger import get_logger
from sqlalchemy import text
from uuid_utils import uuid7

logger = get_logger(__name__)

ACTIVE_YEARS = (2021, 2023)
EXPECTED_COUNTS_BY_YEAR = {
    2021: 8,
    2023: 102,
}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS_BY_YEAR.values())

REQUIRED_OPERATORS = OrderedDict(
    {
        "EQUAL": "Dos valores son iguales.",
        "GREATER_THAN": "Un valor es mayor que otro.",
        "CONTAINS": "Un conjunto de valores contiene el valor esperado.",
    }
)

BOOLEAN_TYPE = "BOOLEAN"
NUMERIC_TYPE = "NUMERIC"
MULTI_CHOICE_TYPE = "MULTI_CHOICE"

DIRECT_GROUP = "DIRECT"
CARD_GROUP = "CARD"


# -----------------------------------------------------------------------------
# CARGA DEL POBLADOR DE FIELDS
# -----------------------------------------------------------------------------


def load_fields_module():
    """Carga 11h para reutilizar exactamente la interpretación del Excel."""
    module_path = Path(__file__).with_name("11h_seed_fields.py")

    if not module_path.is_file():
        raise FileNotFoundError(
            "No se encontró 11h_seed_fields.py en la misma carpeta de 12a. "
            f"Ruta esperada: {module_path}"
        )

    spec = importlib.util.spec_from_file_location(
        "iip_seed_fields_for_dependencies",
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


def normalize_text(value):
    return H.normalize_text(value)


def is_uuidv7(value) -> bool:
    try:
        return UUID(str(value)).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    return str(uuid7())


def canonical_json(value: dict[str, Any] | str) -> str:
    """Representación estable para comparar JSONB.

    PostgreSQL normalmente devuelve JSONB como dict, pero algunos drivers o
    configuraciones pueden devolverlo como texto JSON.
    """
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = value
    else:
        parsed = value

    return json.dumps(
        parsed,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def field_key(
    year: int,
    question_code: str,
    group_kind: str,
    display_order: int,
) -> tuple[int, str, str, int]:
    return (
        int(year),
        normalize_text(question_code),
        group_kind,
        int(display_order),
    )


def assert_expected_type(
    fields: dict[tuple[int, str, str, int], dict],
    key: tuple[int, str, str, int],
    expected_type: str,
    context: str,
) -> None:
    field = fields.get(key)
    if field is None:
        raise ValueError(f"No existe el field requerido para {context}: {key}")

    real_type = field["field_type_label"]
    if real_type != expected_type:
        raise ValueError(
            f"Tipo de field incorrecto para {context}. "
            f"Esperado={expected_type}; SQL={real_type}; key={key}."
        )


# -----------------------------------------------------------------------------
# CONSTRUCCIÓN DE DEPENDENCIAS ESPERADAS
# -----------------------------------------------------------------------------


def build_dependency_blueprints(
    loops: OrderedDict[str, dict],
    field_specs: list[dict],
) -> list[dict]:
    """Construye las 110 dependencias metodológicamente documentadas."""
    specs_by_key: dict[tuple[int, str, str, int], dict] = {}
    card_orders_by_question: dict[str, list[int]] = defaultdict(list)

    for spec in field_specs:
        key = field_key(
            spec["year"],
            spec["question_code"],
            spec["group_kind"],
            spec["display_order"],
        )

        if key in specs_by_key:
            raise ValueError(
                f"La interpretación del Excel produjo un field duplicado: {key}"
            )

        specs_by_key[key] = spec

        if spec["year"] == 2023 and spec["group_kind"] == CARD_GROUP:
            card_orders_by_question[spec["question_code"]].append(
                int(spec["display_order"])
            )

    dependencies: list[dict] = []

    def add_dependency(
        *,
        year: int,
        target_question: str,
        target_group: str,
        target_order: int,
        controller_question: str,
        controller_group: str,
        controller_order: int,
        operator: str,
        expected_value: dict | None = None,
        choice_order: int | None = None,
        reason: str,
    ) -> None:
        target = field_key(
            year,
            target_question,
            target_group,
            target_order,
        )
        controller = field_key(
            year,
            controller_question,
            controller_group,
            controller_order,
        )

        if target not in specs_by_key:
            raise ValueError(
                f"No existe el target field definido por el Excel: {target}"
            )
        if controller not in specs_by_key:
            raise ValueError(
                "No existe el controller field definido por el Excel: "
                f"{controller}"
            )

        dependencies.append(
            {
                "year": int(year),
                "target_key": target,
                "controller_key": controller,
                "operator_label": operator,
                "expected_value": expected_value,
                "choice_order": choice_order,
                "reason": reason,
            }
        )

    # ------------------------------------------------------------------
    # IIP 2021: flujo Preguntas 21 a 23.
    # ------------------------------------------------------------------

    q21_boolean = ("Pregunta 21", DIRECT_GROUP, 1)
    q211_numeric = ("Pregunta 21.1", DIRECT_GROUP, 1)
    q213_boolean = ("Pregunta 21.3", DIRECT_GROUP, 1)

    # Pregunta 21.1 solo aparece cuando Pregunta 21 = Sí.
    add_dependency(
        year=2021,
        target_question="Pregunta 21.1",
        target_group=DIRECT_GROUP,
        target_order=1,
        controller_question=q21_boolean[0],
        controller_group=q21_boolean[1],
        controller_order=q21_boolean[2],
        operator="EQUAL",
        expected_value={"value": True},
        reason="Mostrar cantidad de innovaciones cuando Pregunta 21 sea Sí.",
    )

    # El segundo campo de 21.1 y las preguntas 21.2, 21.3, 22 y 23 se
    # muestran cuando la cantidad de innovaciones es mayor que cero.
    for target_question, target_order in (
        ("Pregunta 21.1", 2),
        ("Pregunta 21.2", 1),
        ("Pregunta 21.3", 1),
        ("Pregunta 22", 1),
        ("Pregunta 23", 1),
    ):
        add_dependency(
            year=2021,
            target_question=target_question,
            target_group=DIRECT_GROUP,
            target_order=target_order,
            controller_question=q211_numeric[0],
            controller_group=q211_numeric[1],
            controller_order=q211_numeric[2],
            operator="GREATER_THAN",
            expected_value={"value": 0},
            reason=(
                f"Mostrar {target_question} cuando la cantidad de innovaciones "
                "de Pregunta 21.1 sea mayor que cero."
            ),
        )

    # 21.4 y 21.5 solo aplican cuando se desarrolló prototipo.
    for target_question in ("Pregunta 21.4", "Pregunta 21.5"):
        add_dependency(
            year=2021,
            target_question=target_question,
            target_group=DIRECT_GROUP,
            target_order=1,
            controller_question=q213_boolean[0],
            controller_group=q213_boolean[1],
            controller_order=q213_boolean[2],
            operator="EQUAL",
            expected_value={"value": True},
            reason=(
                f"Mostrar {target_question} cuando Pregunta 21.3 sea Sí."
            ),
        )

    # ------------------------------------------------------------------
    # IIP 2023: selector auxiliar de Pregunta 24.
    # ------------------------------------------------------------------

    add_dependency(
        year=2023,
        target_question="Pregunta 24",
        target_group=DIRECT_GROUP,
        target_order=2,
        controller_question="Pregunta 24",
        controller_group=DIRECT_GROUP,
        controller_order=1,
        operator="EQUAL",
        expected_value={"value": True},
        reason=(
            "Mostrar el selector de actividades cuando Pregunta 24 sea Sí."
        ),
    )

    # ------------------------------------------------------------------
    # IIP 2023: 27 tarjetas repetibles.
    # ------------------------------------------------------------------

    q24_loop_to_choice_order = {
        "Pregunta 24.1": 1,
        "Pregunta 24.2": 2,
        "Pregunta 24.3": 3,
        "Pregunta 24.4": 4,
        "Pregunta 24.5": 5,
    }

    for loop_code, loop in loops.items():
        target_orders = sorted(card_orders_by_question.get(loop_code, []))

        if not target_orders:
            raise ValueError(
                f"El bucle {loop_code} no tiene fields CARD en 11h."
            )

        if loop_code in q24_loop_to_choice_order:
            choice_order = q24_loop_to_choice_order[loop_code]

            for target_order in target_orders:
                add_dependency(
                    year=2023,
                    target_question=loop_code,
                    target_group=CARD_GROUP,
                    target_order=target_order,
                    controller_question="Pregunta 24",
                    controller_group=DIRECT_GROUP,
                    controller_order=2,
                    operator="CONTAINS",
                    expected_value=None,
                    choice_order=choice_order,
                    reason=(
                        f"Mostrar el field {target_order} de {loop_code} cuando "
                        f"el selector de Pregunta 24 contenga la opción "
                        f"{choice_order}."
                    ),
                )
            continue

        parent_question = loop["parent_code"]

        for target_order in target_orders:
            add_dependency(
                year=2023,
                target_question=loop_code,
                target_group=CARD_GROUP,
                target_order=target_order,
                controller_question=parent_question,
                controller_group=DIRECT_GROUP,
                controller_order=1,
                operator="EQUAL",
                expected_value={"value": True},
                reason=(
                    f"Mostrar el field {target_order} de {loop_code} cuando "
                    f"{parent_question} sea Sí."
                ),
            )

    counts = defaultdict(int)
    target_keys = set()

    for dependency in dependencies:
        counts[dependency["year"]] += 1
        target = dependency["target_key"]

        # En el alcance actual cada target tiene una única condición.
        if target in target_keys:
            raise ValueError(
                f"Se construyeron varias dependencias para el mismo target: {target}"
            )
        target_keys.add(target)

    if dict(counts) != EXPECTED_COUNTS_BY_YEAR:
        raise ValueError(
            "Conteos de dependencias inesperados. "
            f"Esperado={EXPECTED_COUNTS_BY_YEAR}; obtenido={dict(counts)}"
        )

    if len(dependencies) != EXPECTED_TOTAL:
        raise ValueError(
            f"Se esperaban {EXPECTED_TOTAL} dependencias y se construyeron "
            f"{len(dependencies)}."
        )

    return dependencies


# -----------------------------------------------------------------------------
# POSTGRESQL
# -----------------------------------------------------------------------------


async def get_table_columns(conn, schema: str, table: str) -> dict:
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
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
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


async def validate_schema(conn) -> None:
    columns = await get_table_columns(conn, "rules", "field_dependencies")
    required = {
        "id",
        "target_field_id",
        "depends_on_field_id",
        "relational_operator_id",
        "expected_value",
    }
    missing = required - set(columns)
    if missing:
        raise ValueError(
            "rules.field_dependencies no tiene las columnas requeridas. "
            f"Faltan: {sorted(missing)}"
        )

    await get_table_columns(conn, "reference", "relational_operators")


async def ensure_relational_operators(conn) -> dict[str, str]:
    """Obtiene o crea EQUAL, GREATER_THAN y CONTAINS."""
    result = await conn.execute(
        text(
            """
            SELECT
                UPPER(TRIM(label)) AS label,
                id::text AS operator_id,
                description
            FROM reference.relational_operators
            ORDER BY label, id;
            """
        )
    )

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[row["label"]].append(dict(row))

    lookup: dict[str, str] = {}

    for label, description in REQUIRED_OPERATORS.items():
        rows = grouped.get(label, [])

        if len(rows) > 1:
            raise ValueError(
                f"Existen operadores relacionales duplicados para {label}: "
                f"{[row['operator_id'] for row in rows]}"
            )

        if rows:
            operator_id = rows[0]["operator_id"]
            if not is_uuidv7(operator_id):
                raise ValueError(
                    f"El operador {label} no tiene UUIDv7: {operator_id}"
                )

            # Mantiene la descripción uniforme sin cambiar el UUID.
            await conn.execute(
                text(
                    """
                    UPDATE reference.relational_operators
                    SET description = :description
                    WHERE id = CAST(:id AS uuid);
                    """
                ),
                {"id": operator_id, "description": description},
            )
            lookup[label] = operator_id
            continue

        operator_id = new_uuidv7()
        await conn.execute(
            text(
                """
                INSERT INTO reference.relational_operators (
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
                "id": operator_id,
                "label": label,
                "description": description,
            },
        )
        lookup[label] = operator_id
        logger.info(f"Creado relational_operator {label}: {operator_id}")

    return lookup


async def load_fields(conn) -> dict[tuple[int, str, str, int], dict]:
    """Relaciona fields por año, pregunta, tipo de grupo y orden."""
    result = await conn.execute(
        text(
            """
            SELECT
                field.id::text AS field_id,
                field.form_id::text AS field_form_id,
                field.field_group_id::text AS field_group_id,
                field.display_order,

                UPPER(TRIM(field_type.label)) AS field_type_label,

                field_group.form_id::text AS group_form_id,
                field_group.question_id::text AS question_id,
                field_group.card_template_id::text AS card_template_id,

                question.form_id::text AS question_form_id,
                question.label AS question_label,

                form.code

            FROM forms.fields field

            JOIN reference.field_types field_type
                ON field_type.id = field.field_type_id

            JOIN forms.field_groups field_group
                ON field_group.id = field.field_group_id

            JOIN forms.questions question
                ON question.id = field_group.question_id

            JOIN forms.forms form
                ON form.id = question.form_id

            WHERE form.code IN (2021, 2023)

            ORDER BY
                form.code,
                question.label,
                field_group.card_template_id,
                field.display_order,
                field.id;
            """
        )
    )

    lookup: dict[tuple[int, str, str, int], dict] = {}

    for row in result.mappings().all():
        field_id = row["field_id"]

        if not is_uuidv7(field_id):
            raise ValueError(f"Field sin UUIDv7: {field_id}")

        if not is_uuidv7(row["field_form_id"]):
            raise ValueError(
                f"form_id no UUIDv7 para field {field_id}: "
                f"{row['field_form_id']}"
            )

        if row["field_form_id"] != row["group_form_id"]:
            raise ValueError(
                f"Field {field_id} y field_group pertenecen a forms distintos."
            )

        if row["field_form_id"] != row["question_form_id"]:
            raise ValueError(
                f"Field {field_id} y question pertenecen a forms distintos."
            )

        group_kind = (
            DIRECT_GROUP
            if row["card_template_id"] is None
            else CARD_GROUP
        )

        key = field_key(
            int(row["code"]),
            row["question_label"],
            group_kind,
            int(row["display_order"]),
        )

        if key in lookup:
            raise ValueError(
                f"Hay más de un field para la llave {key}: "
                f"{lookup[key]['field_id']} y {field_id}."
            )

        lookup[key] = {
            "field_id": field_id,
            "form_id": row["field_form_id"],
            "question_id": row["question_id"],
            "question_label": row["question_label"],
            "group_kind": group_kind,
            "display_order": int(row["display_order"]),
            "field_type_label": row["field_type_label"],
        }

    if not lookup:
        raise ValueError(
            "No se encontraron fields para 2021 y 2023. "
            "Ejecuta primero 11h_seed_fields.py."
        )

    return lookup


async def load_choices_for_field(
    conn,
    field_id: str,
) -> dict[int, dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                id::text AS choice_id,
                label,
                description,
                display_order
            FROM forms.field_choices
            WHERE field_id = CAST(:field_id AS uuid)
            ORDER BY display_order, id;
            """
        ),
        {"field_id": field_id},
    )

    lookup: dict[int, dict] = {}
    for row in result.mappings().all():
        order = int(row["display_order"])

        if order in lookup:
            raise ValueError(
                f"La opción {order} está duplicada para field {field_id}."
            )

        if not is_uuidv7(row["choice_id"]):
            raise ValueError(
                f"Field choice sin UUIDv7: {row['choice_id']}"
            )

        lookup[order] = dict(row)

    return lookup


async def resolve_dependencies(
    conn,
    blueprints: list[dict],
    fields: dict[tuple[int, str, str, int], dict],
    operators: dict[str, str],
) -> list[dict]:
    """Reemplaza llaves lógicas por UUIDv7 reales."""
    resolved: list[dict] = []
    choices_cache: dict[str, dict[int, dict]] = {}

    for source in blueprints:
        target = fields.get(source["target_key"])
        controller = fields.get(source["controller_key"])

        if target is None:
            raise ValueError(
                f"No se encontró target field en SQL: {source['target_key']}"
            )
        if controller is None:
            raise ValueError(
                "No se encontró depends_on field en SQL: "
                f"{source['controller_key']}"
            )

        if target["form_id"] != controller["form_id"]:
            raise ValueError(
                "Una dependencia no puede cruzar formularios. "
                f"Target={source['target_key']}; "
                f"Controller={source['controller_key']}."
            )

        operator_label = source["operator_label"]
        operator_id = operators.get(operator_label)
        if operator_id is None:
            raise ValueError(
                f"No se encontró relational_operator {operator_label}."
            )

        expected_value = source["expected_value"]

        if operator_label == "EQUAL":
            assert_expected_type(
                fields,
                source["controller_key"],
                BOOLEAN_TYPE,
                source["reason"],
            )

        elif operator_label == "GREATER_THAN":
            assert_expected_type(
                fields,
                source["controller_key"],
                NUMERIC_TYPE,
                source["reason"],
            )

        elif operator_label == "CONTAINS":
            assert_expected_type(
                fields,
                source["controller_key"],
                MULTI_CHOICE_TYPE,
                source["reason"],
            )

            controller_id = controller["field_id"]
            if controller_id not in choices_cache:
                choices_cache[controller_id] = await load_choices_for_field(
                    conn,
                    controller_id,
                )

            choice_order = int(source["choice_order"])
            choice = choices_cache[controller_id].get(choice_order)
            if choice is None:
                raise ValueError(
                    f"No existe la opción {choice_order} para el selector "
                    f"{source['controller_key']}."
                )

            expected_value = {"choice_id": choice["choice_id"]}

        else:
            raise ValueError(f"Operador no soportado: {operator_label}")

        if not isinstance(expected_value, dict) or not expected_value:
            raise ValueError(
                f"expected_value inválido para {source['reason']}: "
                f"{expected_value!r}"
            )

        resolved.append(
            {
                "year": source["year"],
                "target_field_id": target["field_id"],
                "depends_on_field_id": controller["field_id"],
                "relational_operator_id": operator_id,
                "operator_label": operator_label,
                "expected_value": expected_value,
                "expected_value_json": canonical_json(expected_value),
                "reason": source["reason"],
            }
        )

    return resolved


async def load_existing_dependencies(
    conn,
    target_field_ids: set[str],
) -> dict[str, dict]:
    """Obtiene dependencias existentes para los targets que administra 12a.

    El alcance actual define una sola condición por target. Si encuentra más de
    una, detiene la carga para no eliminar reglas manuales de forma silenciosa.
    """
    if not target_field_ids:
        return {}

    result = await conn.execute(
        text(
            """
            SELECT
                dependency.id::text AS dependency_id,
                dependency.target_field_id::text AS target_field_id,
                dependency.depends_on_field_id::text AS depends_on_field_id,
                dependency.relational_operator_id::text AS relational_operator_id,
                dependency.expected_value
            FROM rules.field_dependencies dependency
            JOIN forms.fields target
                ON target.id = dependency.target_field_id
            JOIN forms.forms form
                ON form.id = target.form_id
            WHERE form.code IN (2021, 2023)
            ORDER BY dependency.target_field_id, dependency.id;
            """
        )
    )

    grouped: dict[str, list[dict]] = defaultdict(list)

    for row in result.mappings().all():
        target_id = row["target_field_id"]
        if target_id not in target_field_ids:
            continue
        grouped[target_id].append(dict(row))

    existing: dict[str, dict] = {}

    for target_id, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                "Existen varias dependencias para un target administrado por "
                f"12a: target_field_id={target_id}; "
                f"ids={[row['dependency_id'] for row in rows]}."
            )

        dependency_id = rows[0]["dependency_id"]
        if not is_uuidv7(dependency_id):
            raise ValueError(
                f"La dependencia existente no tiene UUIDv7: {dependency_id}"
            )

        existing[target_id] = rows[0]

    return existing


async def save_dependencies(
    conn,
    dependencies: list[dict],
) -> tuple[int, int]:
    target_ids = {
        dependency["target_field_id"]
        for dependency in dependencies
    }
    existing = await load_existing_dependencies(conn, target_ids)

    inserted = 0
    updated = 0

    for dependency in dependencies:
        old = existing.get(dependency["target_field_id"])

        params = {
            "id": (
                old["dependency_id"]
                if old is not None
                else new_uuidv7()
            ),
            "target_field_id": dependency["target_field_id"],
            "depends_on_field_id": dependency["depends_on_field_id"],
            "relational_operator_id": dependency["relational_operator_id"],
            "expected_value": dependency["expected_value_json"],
        }

        if old is not None:
            await conn.execute(
                text(
                    """
                    UPDATE rules.field_dependencies
                    SET
                        target_field_id = CAST(:target_field_id AS uuid),
                        depends_on_field_id = CAST(:depends_on_field_id AS uuid),
                        relational_operator_id = CAST(
                            :relational_operator_id AS uuid
                        ),
                        expected_value = CAST(:expected_value AS jsonb)
                    WHERE id = CAST(:id AS uuid);
                    """
                ),
                params,
            )
            updated += 1
        else:
            await conn.execute(
                text(
                    """
                    INSERT INTO rules.field_dependencies (
                        id,
                        target_field_id,
                        depends_on_field_id,
                        relational_operator_id,
                        expected_value
                    )
                    VALUES (
                        CAST(:id AS uuid),
                        CAST(:target_field_id AS uuid),
                        CAST(:depends_on_field_id AS uuid),
                        CAST(:relational_operator_id AS uuid),
                        CAST(:expected_value AS jsonb)
                    );
                    """
                ),
                params,
            )
            inserted += 1

    return inserted, updated


# -----------------------------------------------------------------------------
# VALIDACIÓN POSTERIOR
# -----------------------------------------------------------------------------


async def validate_loaded_dependencies(
    conn,
    expected: list[dict],
) -> None:
    expected_by_target = {
        item["target_field_id"]: item
        for item in expected
    }

    result = await conn.execute(
        text(
            """
            SELECT
                dependency.id::text AS dependency_id,
                dependency.target_field_id::text AS target_field_id,
                dependency.depends_on_field_id::text AS depends_on_field_id,
                dependency.relational_operator_id::text AS relational_operator_id,
                dependency.expected_value,

                UPPER(TRIM(operator.label)) AS operator_label,

                target.form_id::text AS target_form_id,
                controller.form_id::text AS controller_form_id,
                form.code

            FROM rules.field_dependencies dependency

            JOIN forms.fields target
                ON target.id = dependency.target_field_id

            JOIN forms.fields controller
                ON controller.id = dependency.depends_on_field_id

            JOIN reference.relational_operators operator
                ON operator.id = dependency.relational_operator_id

            JOIN forms.forms form
                ON form.id = target.form_id

            WHERE form.code IN (2021, 2023)

            ORDER BY form.code, dependency.target_field_id, dependency.id;
            """
        )
    )

    loaded_by_target: dict[str, dict] = {}

    for row in result.mappings().all():
        target_id = row["target_field_id"]
        if target_id not in expected_by_target:
            continue

        if target_id in loaded_by_target:
            raise ValueError(
                f"El target {target_id} tiene más de una dependencia cargada."
            )

        loaded_by_target[target_id] = dict(row)

    missing = set(expected_by_target) - set(loaded_by_target)
    if missing:
        raise ValueError(
            "No se cargaron todas las dependencias esperadas. "
            f"Targets faltantes: {sorted(missing)[:20]}"
        )

    counts = defaultdict(int)

    for target_id, expected_item in expected_by_target.items():
        row = loaded_by_target[target_id]
        counts[int(row["code"])] += 1

        if not is_uuidv7(row["dependency_id"]):
            raise ValueError(
                "Dependencia sin UUIDv7: "
                f"{row['dependency_id']}"
            )

        if row["target_form_id"] != row["controller_form_id"]:
            raise ValueError(
                f"La dependencia {row['dependency_id']} cruza formularios."
            )

        if row["depends_on_field_id"] != expected_item["depends_on_field_id"]:
            raise ValueError(
                f"depends_on_field_id incorrecto para target {target_id}."
            )

        if row["relational_operator_id"] != expected_item[
            "relational_operator_id"
        ]:
            raise ValueError(
                f"relational_operator_id incorrecto para target {target_id}."
            )

        if row["operator_label"] != expected_item["operator_label"]:
            raise ValueError(
                f"Operador incorrecto para target {target_id}: "
                f"SQL={row['operator_label']}; "
                f"esperado={expected_item['operator_label']}."
            )

        real_expected = row["expected_value"]
        if canonical_json(real_expected) != expected_item[
            "expected_value_json"
        ]:
            raise ValueError(
                f"expected_value incorrecto para target {target_id}. "
                f"SQL={real_expected}; "
                f"esperado={expected_item['expected_value']}."
            )

    if dict(counts) != EXPECTED_COUNTS_BY_YEAR:
        raise ValueError(
            "Validación de conteos falló. "
            f"Esperado={EXPECTED_COUNTS_BY_YEAR}; obtenido={dict(counts)}"
        )

    logger.info(
        "rules.field_dependencies validation passed. "
        f"Validated dependencies: {len(expected_by_target)}."
    )


# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    """Puebla rules.field_dependencies."""

    excel_path = Path(H.FILE_PATH)
    if not excel_path.is_file():
        raise FileNotFoundError(
            f"No existe el archivo de estructura IIP: {excel_path}"
        )

    logger.info(
        "Starting rules.field_dependencies population from "
        f"{excel_path}."
    )
    print(f"[12a] Archivo Excel: {excel_path}", flush=True)

    _, loops, _, field_specs = H.load_instrument(excel_path)
    blueprints = build_dependency_blueprints(loops, field_specs)

    print(
        "[12a] Dependencias construidas: "
        "2021=8, 2023=102, total=110.",
        flush=True,
    )

    async with async_engine.begin() as conn:
        await validate_schema(conn)
        operators = await ensure_relational_operators(conn)
        fields = await load_fields(conn)
        dependencies = await resolve_dependencies(
            conn,
            blueprints,
            fields,
            operators,
        )
        inserted, updated = await save_dependencies(conn, dependencies)
        await validate_loaded_dependencies(conn, dependencies)

    logger.info(
        "rules.field_dependencies population completed successfully. "
        f"Inserted={inserted}; updated={updated}; total={len(dependencies)}."
    )
    print(
        f"[12a] OK. Insertados={inserted}; actualizados={updated}; "
        f"total={len(dependencies)}.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
