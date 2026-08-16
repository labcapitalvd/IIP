"""Puebla forms.fields para los IIP 2019, 2021 y 2023.

Dependencias previas:
    11d_seed_questions.py
    11e_seed_loop_questions.py
    11f_seed_card_templates.py
    11g_seed_field_groups.py

Convención de almacenamiento:
- label: número corto del campo dentro de su grupo: "1", "2", "3", etc.
- description: enunciado completo de la pregunta o subpregunta.
- required: TRUE, salvo campos de tipo texto_calculado.
- display_order: orden del campo dentro del grupo.
- No se almacenan ponderaciones Maxp, Maxb, Max_subpregunta_bucle ni
  información técnica en description.

La fuente de verdad es Estructura_IIP.xlsx. El script no depende de helper en
questions, sections o card_templates.
"""

from __future__ import annotations

import asyncio
import os
import re
import unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path
from uuid import UUID

import pandas as pd
from shared.infrastructure import async_engine
from shared.utils.logger import get_logger
from sqlalchemy import text
from uuid_utils import uuid7

logger = get_logger(__name__)

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)
ACTIVE_YEARS = (2019, 2021, 2023)

FIELD_TYPE_DESCRIPTIONS = {
    "BOOLEAN": "AnswerBoolean",
    "CARD": "AnswerCardEntry",
    "DATE": "AnswerDate",
    "FILE": "AnswerFile",
    "MULTI_CHOICE": "AnswerMultiChoice",
    "NUMERIC": "AnswerNumeric",
    "SINGLE_CHOICE": "AnswerSingleChoice",
    "TEXT": "AnswerText",
}

DATA_TYPE_TO_FIELD_TYPE = {
    "booleano": "BOOLEAN",
    "entero": "NUMERIC",
    "monetario": "NUMERIC",
    "decimal": "NUMERIC",
    "porcentaje": "NUMERIC",
    "categorico": "SINGLE_CHOICE",
    "rango_ordinal": "SINGLE_CHOICE",
    "seleccion_multiple": "MULTI_CHOICE",
    "texto": "TEXT",
    "texto_calculado": "TEXT",
    "archivo": "FILE",
    "fecha": "DATE",
}

EXPECTED_FIELD_COUNTS = {
    (2019, "DIRECT"): 43,
    (2021, "DIRECT"): 53,
    (2023, "DIRECT"): 48,
    (2023, "CARD"): 101,
}


# -----------------------------------------------------------------------------
# UTILIDADES PÚBLICAS (11i reutiliza estas funciones)
# -----------------------------------------------------------------------------


def clean(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    value = str(value).strip()
    return value or None


def normalize_text(value):
    value = clean(value)
    if value is None:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_token(value):
    value = normalize_text(value)
    if value is None:
        return None
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def is_uuidv7(value) -> bool:
    try:
        return UUID(str(value)).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    return str(uuid7())


def truncate(value, max_length):
    value = clean(value)
    if value is None or max_length is None:
        return value
    return value[:max_length]


def unique_in_order(values) -> list:
    output = []
    seen = set()
    for value in values:
        value = clean(value)
        if value is None:
            continue
        key = normalize_text(value)
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output


def parse_positive_integer(value, context: str) -> int:
    value = clean(value)
    if value is None:
        raise ValueError(f"Valor vacío en {context}.")
    try:
        numeric = float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Valor inválido en {context}: {value!r}") from exc
    if not numeric.is_integer() or numeric <= 0:
        raise ValueError(f"Valor inválido en {context}: {value!r}")
    return int(numeric)


def read_sheet(excel: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    if sheet_name not in excel.sheet_names:
        raise ValueError(
            f"No existe la hoja {sheet_name!r}. "
            f"Hojas disponibles: {excel.sheet_names}"
        )
    frame = pd.read_excel(excel, sheet_name=sheet_name, dtype=object)
    frame.columns = [str(column).strip() for column in frame.columns]
    return frame


def map_field_type(data_type: str) -> str:
    token = normalize_token(data_type)
    field_type = DATA_TYPE_TO_FIELD_TYPE.get(token)
    if field_type is None:
        raise ValueError(
            f"Tipo_dato sin mapeo: {data_type!r} "
            f"(normalizado={token!r})."
        )
    return field_type


def field_required(data_type: str) -> bool:
    return normalize_token(data_type) != "texto_calculado"


# -----------------------------------------------------------------------------
# LECTURA DEL INSTRUMENTO
# -----------------------------------------------------------------------------


def load_structure(
    excel: pd.ExcelFile,
) -> tuple[dict[int, OrderedDict[str, str]], OrderedDict[str, dict]]:
    """Obtiene preguntas principales y definiciones de bucle."""
    main_questions: dict[int, OrderedDict[str, str]] = {}

    for year in ACTIVE_YEARS:
        frame = read_sheet(excel, str(year))
        required = {"Pregunta", f"Pregunta {year}"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"Faltan columnas en la hoja {year}: {sorted(missing)}"
            )

        registry: OrderedDict[str, str] = OrderedDict()
        for _, row in frame.iterrows():
            question_code = clean(row["Pregunta"])
            question_text = clean(row[f"Pregunta {year}"])
            if question_code is None or question_text is None:
                continue

            old = registry.get(question_code)
            if old is not None and normalize_text(old) != normalize_text(question_text):
                raise ValueError(
                    f"Textos contradictorios para {question_code} en {year}."
                )
            registry.setdefault(question_code, question_text)

        if not registry:
            raise ValueError(f"La hoja {year} no produjo preguntas.")
        main_questions[year] = registry

    frame_2023 = read_sheet(excel, "2023")
    required_loops = {
        "Pregunta",
        "Bucle",
        "Bucle 2023",
        "Orden_subpregunta_bucle",
        "Subpregunta_bucle",
    }
    missing = required_loops - set(frame_2023.columns)
    if missing:
        raise ValueError(
            f"Faltan columnas de bucle en 2023: {sorted(missing)}"
        )

    loops: OrderedDict[str, dict] = OrderedDict()

    for index, row in frame_2023.iterrows():
        loop_code = clean(row["Bucle"])
        if loop_code is None:
            continue

        loop_text = clean(row["Bucle 2023"])
        parent_code = clean(row["Pregunta"])
        subquestion_text = clean(row["Subpregunta_bucle"])

        if loop_text is None or parent_code is None:
            raise ValueError(
                f"Bucle incompleto en fila {int(index) + 2}: {loop_code}."
            )

        item = loops.setdefault(
            loop_code,
            {
                "loop_code": loop_code,
                "loop_text": loop_text,
                "parent_code": parent_code,
                "is_mixed": loop_code == parent_code,
                "subquestions": OrderedDict(),
            },
        )

        if (
            normalize_text(item["loop_text"]) != normalize_text(loop_text)
            or normalize_text(item["parent_code"]) != normalize_text(parent_code)
        ):
            raise ValueError(
                f"Información contradictoria para {loop_code}."
            )

        if subquestion_text is None:
            continue

        order = parse_positive_integer(
            row["Orden_subpregunta_bucle"],
            f"Orden_subpregunta_bucle de {loop_code}, fila {int(index) + 2}",
        )
        previous = item["subquestions"].get(order)
        if previous is not None and normalize_text(previous) != normalize_text(
            subquestion_text
        ):
            raise ValueError(
                f"Orden {order} repetido con textos distintos en {loop_code}."
            )
        item["subquestions"][order] = subquestion_text

    for loop_code, item in loops.items():
        orders = sorted(item["subquestions"])
        if orders != list(range(1, len(orders) + 1)):
            raise ValueError(
                f"Órdenes no consecutivos en {loop_code}: {orders}"
            )
        item["subquestions"] = [
            {
                "order": order,
                "text": item["subquestions"][order],
            }
            for order in orders
        ]

    if len(loops) != 27:
        raise ValueError(
            f"Se esperaban 27 bucles y se encontraron {len(loops)}."
        )
    if sum(len(item["subquestions"]) for item in loops.values()) != 101:
        raise ValueError(
            "La suma de subpreguntas de bucle debe ser 101."
        )

    return main_questions, loops


def load_responses(
    excel: pd.ExcelFile,
) -> dict[int, OrderedDict[str, OrderedDict[str | None, dict]]]:
    """Agrupa cada hoja de respuestas por pregunta y Texto_subpregunta."""
    output: dict[int, OrderedDict[str, OrderedDict[str | None, dict]]] = {}

    for year in ACTIVE_YEARS:
        sheet_name = f"Respuestas_{year}"
        frame = read_sheet(excel, sheet_name)
        required = {
            "Pregunta",
            "Texto_pregunta",
            "Tipo_pregunta",
            "Tipo_dato",
            "Orden_opcion",
            "Texto_opcion",
            "Valor_maximo",
        }
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"Faltan columnas en {sheet_name}: {sorted(missing)}"
            )

        has_subquestion = "Texto_subpregunta" in frame.columns
        questions: OrderedDict[
            str,
            OrderedDict[str | None, dict],
        ] = OrderedDict()

        for index, row in frame.iterrows():
            question_code = clean(row["Pregunta"])
            question_text = clean(row["Texto_pregunta"])
            data_type = clean(row["Tipo_dato"])
            if question_code is None or question_text is None or data_type is None:
                continue

            subquestion = (
                clean(row["Texto_subpregunta"])
                if has_subquestion
                else None
            )
            group_key = normalize_text(subquestion)
            group = questions.setdefault(question_code, OrderedDict()).setdefault(
                group_key,
                {
                    "subquestion": subquestion,
                    "question_text": question_text,
                    "first_row": int(index) + 2,
                    "rows": [],
                },
            )

            if normalize_text(group["question_text"]) != normalize_text(
                question_text
            ):
                raise ValueError(
                    f"Texto_pregunta contradictorio para {question_code} "
                    f"en {sheet_name}."
                )

            group["rows"].append(
                {
                    "source_sheet": sheet_name,
                    "source_row": int(index) + 2,
                    "question_code": question_code,
                    "question_text": question_text,
                    "subquestion": subquestion,
                    "question_type": clean(row["Tipo_pregunta"]),
                    "data_type": data_type,
                    "option_order": clean(row["Orden_opcion"]),
                    "option_text": clean(row["Texto_opcion"]),
                    "maximum_value": clean(row["Valor_maximo"]),
                }
            )

        output[year] = questions

    return output


def group_definition(group: dict) -> dict:
    data_types = unique_in_order(
        row["data_type"] for row in group["rows"]
    )
    if len(data_types) != 1:
        raise ValueError(
            "Una misma pregunta/subpregunta tiene varios Tipo_dato: "
            f"{data_types}. Fila inicial: {group['first_row']}"
        )

    question_types = unique_in_order(
        row["question_type"] for row in group["rows"]
    )

    return {
        "subquestion": group["subquestion"],
        "question_text": group["question_text"],
        "data_type": data_types[0],
        "question_type": question_types[0] if question_types else None,
        "option_rows": group["rows"],
        "source_sheet": group["rows"][0]["source_sheet"],
        "source_row": group["first_row"],
    }


def strip_option_prefix(value: str) -> str:
    """Elimina un prefijo corto como A. o 1. cuando se usa como texto auxiliar."""
    value = clean(value) or ""
    match = re.match(
        r"^\s*(?:[A-Za-z]|\d+(?:[.,]\d+)*)\s*[\.)]\s*(.*)$",
        value,
    )
    if match and clean(match.group(1)):
        return clean(match.group(1)) or value
    return value


def build_field_specs(
    main_questions: dict[int, OrderedDict[str, str]],
    loops: OrderedDict[str, dict],
    responses: dict[int, OrderedDict[str, OrderedDict[str | None, dict]]],
) -> list[dict]:
    """Convierte el instrumento en una lista determinista de fields."""
    specs: list[dict] = []

    # 2019 y 2021: un campo por pregunta, salvo Pregunta 21.1 de 2021.
    for year in (2019, 2021):
        for question_code, question_text in main_questions[year].items():
            groups = responses[year].get(question_code)
            if not groups:
                raise ValueError(
                    f"{question_code} de {year} no aparece en "
                    f"Respuestas_{year}."
                )

            all_rows = [
                row
                for group in groups.values()
                for row in group["rows"]
            ]

            if year == 2021 and question_code == "Pregunta 21.1":
                if len(all_rows) < 2:
                    raise ValueError(
                        "Pregunta 21.1 de 2021 no contiene sus dos filas."
                    )

                specs.append(
                    {
                        "year": year,
                        "question_code": question_code,
                        "response_question_code": question_code,
                        "group_kind": "DIRECT",
                        "display_order": 1,
                        "description": question_text,
                        "data_type": "entero",
                        "question_type": "Abierta numérica",
                        "option_rows": [],
                    }
                )

                second_description = strip_option_prefix(
                    all_rows[1]["option_text"] or "Nómbrelas"
                )
                specs.append(
                    {
                        "year": year,
                        "question_code": question_code,
                        "response_question_code": question_code,
                        "group_kind": "DIRECT",
                        "display_order": 2,
                        "description": second_description,
                        "data_type": "texto",
                        "question_type": "Abierta texto",
                        "option_rows": [],
                    }
                )
                continue

            data_types = unique_in_order(
                row["data_type"] for row in all_rows
            )
            if len(data_types) != 1:
                raise ValueError(
                    f"{question_code} de {year} tiene varios Tipo_dato: "
                    f"{data_types}"
                )

            question_types = unique_in_order(
                row["question_type"] for row in all_rows
            )

            specs.append(
                {
                    "year": year,
                    "question_code": question_code,
                    "response_question_code": question_code,
                    "group_kind": "DIRECT",
                    "display_order": 1,
                    "description": question_text,
                    "data_type": data_types[0],
                    "question_type": (
                        question_types[0] if question_types else None
                    ),
                    "option_rows": all_rows,
                }
            )

    # 2023: campos directos de las preguntas principales.
    for question_code, question_text in main_questions[2023].items():
        groups = responses[2023].get(question_code)
        if not groups:
            raise ValueError(
                f"{question_code} no aparece en Respuestas_2023."
            )

        definitions = [
            group_definition(group)
            for group in groups.values()
        ]

        # Pregunta 28.1 es mixta: el grupo sin Texto_subpregunta es directo.
        if question_code in loops:
            definitions = [
                definition
                for definition in definitions
                if definition["subquestion"] is None
            ]

        for display_order, definition in enumerate(definitions, start=1):
            specs.append(
                {
                    "year": 2023,
                    "question_code": question_code,
                    "response_question_code": question_code,
                    "group_kind": "DIRECT",
                    "display_order": display_order,
                    "description": (
                        definition["subquestion"] or question_text
                    ),
                    "data_type": definition["data_type"],
                    "question_type": definition["question_type"],
                    "option_rows": definition["option_rows"],
                }
            )

    # Selección múltiple auxiliar de Pregunta 24.1: pertenece a Pregunta 24.
    groups_241 = responses[2023].get("Pregunta 24.1", OrderedDict())
    auxiliary = [
        group_definition(group)
        for group in groups_241.values()
        if group["subquestion"] is not None
        and normalize_text(group["subquestion"]).startswith("pregunta 24.1.")
    ]
    if len(auxiliary) != 1:
        raise ValueError(
            "Se esperaba una única selección múltiple auxiliar en "
            "Pregunta 24.1."
        )

    current_orders = [
        spec["display_order"]
        for spec in specs
        if spec["year"] == 2023
        and spec["question_code"] == "Pregunta 24"
        and spec["group_kind"] == "DIRECT"
    ]
    auxiliary_definition = auxiliary[0]
    specs.append(
        {
            "year": 2023,
            "question_code": "Pregunta 24",
            "response_question_code": "Pregunta 24.1",
            "group_kind": "DIRECT",
            "display_order": max(current_orders, default=0) + 1,
            "description": auxiliary_definition["subquestion"],
            "data_type": auxiliary_definition["data_type"],
            "question_type": auxiliary_definition["question_type"],
            "option_rows": auxiliary_definition["option_rows"],
        }
    )

    # 2023: campos de cada tarjeta repetible.
    for loop_code, loop in loops.items():
        groups = responses[2023].get(loop_code)
        if not groups:
            raise ValueError(
                f"{loop_code} no aparece en Respuestas_2023."
            )

        definitions = [
            group_definition(group)
            for group in groups.values()
            if group["subquestion"] is not None
        ]

        if loop_code == "Pregunta 24.1":
            definitions = [
                definition
                for definition in definitions
                if not normalize_text(definition["subquestion"]).startswith(
                    "pregunta 24.1."
                )
            ]

        expected_subquestions = loop["subquestions"]
        if len(definitions) != len(expected_subquestions):
            raise ValueError(
                f"{loop_code}: la estructura define "
                f"{len(expected_subquestions)} subpreguntas, pero "
                f"Respuestas_2023 contiene {len(definitions)} grupos."
            )

        for expected, definition in zip(expected_subquestions, definitions):
            if normalize_text(expected["text"]) != normalize_text(
                definition["subquestion"]
            ):
                raise ValueError(
                    f"No coincide la subpregunta {expected['order']} de "
                    f"{loop_code}. Estructura={expected['text']!r}; "
                    f"Respuestas={definition['subquestion']!r}."
                )

            specs.append(
                {
                    "year": 2023,
                    "question_code": loop_code,
                    "response_question_code": loop_code,
                    "group_kind": "CARD",
                    "display_order": expected["order"],
                    "description": expected["text"],
                    "data_type": definition["data_type"],
                    "question_type": definition["question_type"],
                    "option_rows": definition["option_rows"],
                }
            )

    counts = defaultdict(int)
    for spec in specs:
        spec["field_type_label"] = map_field_type(spec["data_type"])
        spec["required"] = field_required(spec["data_type"])
        spec["label"] = str(int(spec["display_order"]))
        counts[(spec["year"], spec["group_kind"])] += 1

    if dict(counts) != EXPECTED_FIELD_COUNTS:
        raise ValueError(
            f"Conteos de fields inesperados. Esperado="
            f"{EXPECTED_FIELD_COUNTS}; obtenido={dict(counts)}"
        )

    return specs


def load_instrument(path: Path) -> tuple[
    dict[int, OrderedDict[str, str]],
    OrderedDict[str, dict],
    dict[int, OrderedDict[str, OrderedDict[str | None, dict]]],
    list[dict],
]:
    excel = pd.ExcelFile(path)
    main_questions, loops = load_structure(excel)
    responses = load_responses(excel)
    specs = build_field_specs(main_questions, loops, responses)
    return main_questions, loops, responses, specs


# -----------------------------------------------------------------------------
# POSTGRESQL (funciones reutilizadas por 11i)
# -----------------------------------------------------------------------------


async def table_columns(conn, schema: str, table: str) -> dict:
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
        raise ValueError(f"No existe {schema}.{table}.")
    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


async def ensure_field_types(conn) -> dict[str, str]:
    result = await conn.execute(
        text(
            """
            SELECT UPPER(TRIM(label)) AS label, id::text AS id
            FROM reference.field_types
            ORDER BY label;
            """
        )
    )

    grouped: dict[str, list[str]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[row["label"]].append(row["id"])

    for label, ids in grouped.items():
        if len(ids) > 1:
            raise ValueError(f"field_type duplicado para {label}: {ids}")
        if not is_uuidv7(ids[0]):
            raise ValueError(f"field_type {label} no tiene UUIDv7: {ids[0]}")

    for label, description in FIELD_TYPE_DESCRIPTIONS.items():
        if label in grouped:
            continue

        field_type_id = new_uuidv7()
        await conn.execute(
            text(
                """
                INSERT INTO reference.field_types (
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
                "id": field_type_id,
                "label": label,
                "description": description,
            },
        )
        grouped[label] = [field_type_id]
        logger.info(f"Created reference.field_types: {label}")

    return {
        label: grouped[label][0]
        for label in FIELD_TYPE_DESCRIPTIONS
    }


async def get_forms(conn) -> dict[int, str]:
    result = await conn.execute(
        text(
            """
            SELECT code, id::text AS id
            FROM forms.forms
            WHERE code IN (2019, 2021, 2023)
            ORDER BY code;
            """
        )
    )

    grouped: dict[int, list[str]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[int(row["code"])].append(row["id"])

    lookup: dict[int, str] = {}
    for year in ACTIVE_YEARS:
        ids = grouped.get(year, [])
        if len(ids) != 1:
            raise ValueError(
                f"Debe existir un único formulario para {year}; "
                f"encontrados: {len(ids)}."
            )
        if not is_uuidv7(ids[0]):
            raise ValueError(f"form_id de {year} no es UUIDv7: {ids[0]}")
        lookup[year] = ids[0]

    return lookup


async def get_questions(
    conn,
    main_questions: dict[int, OrderedDict[str, str]],
    loops: OrderedDict[str, dict],
) -> dict[tuple[int, str], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                question.form_id::text AS form_id,
                question.label,
                question.description,
                question.is_loop,
                form.code
            FROM forms.questions question
            JOIN forms.forms form
              ON form.id = question.form_id
            WHERE form.code IN (2019, 2021, 2023)
            ORDER BY form.code, question.label, question.id;
            """
        )
    )

    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[
            (int(row["code"]), normalize_text(row["label"]))
        ].append(dict(row))

    expected = {
        (year, code)
        for year, questions in main_questions.items()
        for code in questions
    }
    expected.update((2023, code) for code in loops)

    lookup: dict[tuple[int, str], dict] = {}
    for year, code in expected:
        key = (year, normalize_text(code))
        rows = grouped.get(key, [])
        if len(rows) != 1:
            raise ValueError(
                f"No se pudo resolver forms.questions para {year} / {code}. "
                f"Coincidencias: {len(rows)}."
            )
        if not is_uuidv7(rows[0]["question_id"]):
            raise ValueError(
                f"question_id de {year}/{code} no es UUIDv7: "
                f"{rows[0]['question_id']}"
            )
        lookup[(year, code)] = rows[0]

    return lookup


async def get_groups(
    conn,
    questions: dict[tuple[int, str], dict],
    main_questions: dict[int, OrderedDict[str, str]],
    loops: OrderedDict[str, dict],
) -> tuple[dict[tuple[int, str], str], dict[str, str]]:
    result = await conn.execute(
        text(
            """
            SELECT
                group_row.id::text AS field_group_id,
                group_row.question_id::text AS question_id,
                group_row.card_template_id::text AS card_template_id,
                group_row.form_id::text AS form_id,
                template.question_id::text AS template_question_id
            FROM forms.field_groups group_row
            LEFT JOIN forms.card_templates template
              ON template.id = group_row.card_template_id
            ORDER BY group_row.question_id,
                     group_row.card_template_id,
                     group_row.id;
            """
        )
    )

    direct_by_question: dict[str, list[dict]] = defaultdict(list)
    card_by_question: dict[str, list[dict]] = defaultdict(list)

    for row in result.mappings().all():
        row_dict = dict(row)
        if row["card_template_id"] is None:
            direct_by_question[row["question_id"]].append(row_dict)
        else:
            card_by_question[row["question_id"]].append(row_dict)

    direct_lookup: dict[tuple[int, str], str] = {}
    for year, year_questions in main_questions.items():
        for question_code in year_questions:
            question = questions[(year, question_code)]
            rows = direct_by_question.get(question["question_id"], [])
            if len(rows) != 1:
                raise ValueError(
                    f"Debe existir un field_group directo para "
                    f"{year}/{question_code}; encontrados: {len(rows)}. "
                    "Ejecuta antes 11g_seed_field_groups.py."
                )
            row = rows[0]
            if not is_uuidv7(row["field_group_id"]):
                raise ValueError(
                    f"field_group directo no UUIDv7: {row['field_group_id']}"
                )
            if row["form_id"] != question["form_id"]:
                raise ValueError(
                    f"form_id incorrecto en grupo directo de {year}/{question_code}."
                )
            direct_lookup[(year, question_code)] = row["field_group_id"]

    card_lookup: dict[str, str] = {}
    for loop_code in loops:
        question = questions[(2023, loop_code)]
        rows = card_by_question.get(question["question_id"], [])
        if len(rows) != 1:
            raise ValueError(
                f"Debe existir un field_group CARD para {loop_code}; "
                f"encontrados: {len(rows)}. Ejecuta antes "
                "11f_seed_card_templates.py y 11g_seed_field_groups.py."
            )
        row = rows[0]
        if not is_uuidv7(row["field_group_id"]):
            raise ValueError(
                f"field_group CARD no UUIDv7: {row['field_group_id']}"
            )
        if row["template_question_id"] != question["question_id"]:
            raise ValueError(
                f"El card_template del grupo de {loop_code} pertenece a otra "
                "pregunta."
            )
        card_lookup[loop_code] = row["field_group_id"]

    return direct_lookup, card_lookup


async def get_existing_fields(conn) -> dict[tuple[str, int], dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                id::text AS field_id,
                form_id::text AS form_id,
                field_group_id::text AS field_group_id,
                field_type_id::text AS field_type_id,
                label,
                description,
                required,
                display_order
            FROM forms.fields
            ORDER BY field_group_id, display_order, id;
            """
        )
    )

    grouped: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        grouped[
            (row["field_group_id"], int(row["display_order"]))
        ].append(dict(row))

    lookup: dict[tuple[str, int], dict] = {}
    for key, rows in grouped.items():
        if len(rows) > 1:
            raise ValueError(
                f"Fields duplicados para grupo/orden {key}: "
                f"{[row['field_id'] for row in rows]}"
            )
        if not is_uuidv7(rows[0]["field_id"]):
            raise ValueError(
                f"field existente no UUIDv7: {rows[0]['field_id']}"
            )
        lookup[key] = rows[0]

    return lookup


async def save_field(conn, record: dict, update: bool) -> None:
    if update:
        statement = text(
            """
            UPDATE forms.fields
            SET
                form_id = CAST(:form_id AS uuid),
                field_group_id = CAST(:field_group_id AS uuid),
                field_type_id = CAST(:field_type_id AS uuid),
                label = :label,
                description = :description,
                required = :required,
                display_order = :display_order,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
            """
        )
    else:
        statement = text(
            """
            INSERT INTO forms.fields (
                id,
                form_id,
                field_group_id,
                field_type_id,
                label,
                description,
                required,
                display_order,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:form_id AS uuid),
                CAST(:field_group_id AS uuid),
                CAST(:field_type_id AS uuid),
                :label,
                :description,
                :required,
                :display_order,
                NOW()
            );
            """
        )
    await conn.execute(statement, record)


async def get_field_map_for_specs(
    conn,
    specs: list[dict],
    direct_groups: dict[tuple[int, str], str],
    card_groups: dict[str, str],
) -> dict[tuple[int, str, str, int], dict]:
    """Devuelve field_id y tipo para cada especificación esperada."""
    result = await conn.execute(
        text(
            """
            SELECT
                field.id::text AS field_id,
                field.field_group_id::text AS field_group_id,
                field.display_order,
                field.label,
                field.description,
                field.required,
                UPPER(TRIM(field_type.label)) AS field_type_label
            FROM forms.fields field
            JOIN reference.field_types field_type
              ON field_type.id = field.field_type_id
            ORDER BY field.field_group_id, field.display_order, field.id;
            """
        )
    )

    by_group_order: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in result.mappings().all():
        by_group_order[
            (row["field_group_id"], int(row["display_order"]))
        ].append(dict(row))

    field_map: dict[tuple[int, str, str, int], dict] = {}
    for spec in specs:
        group_id = (
            direct_groups[(spec["year"], spec["question_code"])]
            if spec["group_kind"] == "DIRECT"
            else card_groups[spec["question_code"]]
        )
        rows = by_group_order.get(
            (group_id, int(spec["display_order"])),
            [],
        )
        if len(rows) != 1:
            raise ValueError(
                f"No se pudo resolver field para {spec['year']} / "
                f"{spec['question_code']} / {spec['group_kind']} / "
                f"orden {spec['display_order']}. Coincidencias: {len(rows)}."
            )
        key = (
            spec["year"],
            spec["question_code"],
            spec["group_kind"],
            int(spec["display_order"]),
        )
        field_map[key] = rows[0]

    return field_map


# -----------------------------------------------------------------------------
# ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:

    path = Path(FILE_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    logger.info(f"Starting forms.fields population from {path}")

    main_questions, loops, responses, specs = load_instrument(path)

    async with async_engine.begin() as conn:
        columns = await table_columns(conn, "forms", "fields")
        required_columns = {
            "id",
            "form_id",
            "field_group_id",
            "field_type_id",
            "label",
            "description",
            "required",
            "display_order",
            "updated_at",
        }
        missing = required_columns - set(columns)
        if missing:
            raise ValueError(
                f"Faltan columnas en forms.fields: {sorted(missing)}"
            )

        forms = await get_forms(conn)
        questions = await get_questions(conn, main_questions, loops)
        direct_groups, card_groups = await get_groups(
            conn,
            questions,
            main_questions,
            loops,
        )
        field_types = await ensure_field_types(conn)
        existing = await get_existing_fields(conn)

        inserted = 0
        updated = 0

        for spec in specs:
            group_id = (
                direct_groups[(spec["year"], spec["question_code"])]
                if spec["group_kind"] == "DIRECT"
                else card_groups[spec["question_code"]]
            )
            natural_key = (group_id, int(spec["display_order"]))
            old = existing.get(natural_key)

            field_id = old["field_id"] if old else new_uuidv7()
            if not is_uuidv7(field_id):
                raise ValueError(f"ID no UUIDv7: {field_id}")

            db_record = {
                "id": field_id,
                "form_id": forms[spec["year"]],
                "field_group_id": group_id,
                "field_type_id": field_types[spec["field_type_label"]],
                "label": truncate(
                    spec["label"], columns["label"]["max_length"]
                ),
                "description": truncate(
                    spec["description"],
                    columns["description"]["max_length"],
                ),
                "required": bool(spec["required"]),
                "display_order": int(spec["display_order"]),
            }

            await save_field(conn, db_record, update=old is not None)
            if old:
                updated += 1
            else:
                inserted += 1

        field_map = await get_field_map_for_specs(
            conn,
            specs,
            direct_groups,
            card_groups,
        )

        for spec in specs:
            key = (
                spec["year"],
                spec["question_code"],
                spec["group_kind"],
                int(spec["display_order"]),
            )
            row = field_map[key]
            if normalize_text(row["label"]) != normalize_text(spec["label"]):
                raise ValueError(f"label incorrecto para field {key}.")
            if normalize_text(row["description"]) != normalize_text(
                spec["description"]
            ):
                raise ValueError(f"description incorrecta para field {key}.")
            if row["field_type_label"] != spec["field_type_label"]:
                raise ValueError(f"field_type incorrecto para field {key}.")
            if row["required"] is not bool(spec["required"]):
                raise ValueError(f"required incorrecto para field {key}.")
            if not is_uuidv7(row["field_id"]):
                raise ValueError(f"UUID no es versión 7 para field {key}.")

    logger.info(
        "forms.fields population finished successfully. "
        f"Inserted: {inserted}. Updated: {updated}. "
        f"Expected: {len(specs)}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
