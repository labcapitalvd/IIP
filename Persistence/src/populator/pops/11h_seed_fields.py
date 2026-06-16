"""Puebla forms.fields para los IIP 2019, 2021 y 2023.

Este poblador es deliberadamente independiente de los helpers generados por
otros scripts. Usa como fuente de verdad Estructura_IIP.xlsx y relaciona los
registros por año + label visible de la pregunta.

Además, repara las dependencias mínimas si están vacías:
- reference.field_types
- forms.card_templates para los bucles de 2023
- forms.field_groups directos y repetibles

Requisitos previos reales:
- forms.forms debe contener 2019, 2021 y 2023.
- forms.questions debe contener las preguntas principales y los bucles de 2023.
- Estructura_IIP.xlsx debe estar disponible dentro del contenedor.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from uuid_utils import uuid7

from shared_db import async_engine
from shared_utils.logger import get_logger


logger = get_logger("pop/fields")

ACTIVE_YEARS = (2019, 2021, 2023)
SOURCE_NAME = "Estructura_IIP.xlsx"

FILE_CANDIDATES = (
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
    "/api/populator/pops/Estructura_IIP.xlsx",
    "/api/populator/Estructura_IIP.xlsx",
)

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


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


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
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_token(value):
    value = normalize_text(value)
    if value is None:
        return None
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def parse_integer(value, context: str) -> int:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raise ValueError(f"Valor entero vacío en {context}.")
    try:
        numeric = float(str(value).replace(",", ".").strip())
    except ValueError as exc:
        raise ValueError(f"Valor entero inválido en {context}: {value!r}") from exc
    if not numeric.is_integer():
        raise ValueError(f"Valor no entero en {context}: {value!r}")
    return int(numeric)


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


def unique_in_order(values):
    result = []
    seen = set()
    for value in values:
        value = clean(value)
        if value is None:
            continue
        key = normalize_text(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def resolve_excel_path() -> Path:
    candidates = []
    configured = clean(os.getenv("IIP_STRUCTURE_FILE"))
    if configured:
        candidates.append(Path(configured))
    candidates.extend(Path(path) for path in FILE_CANDIDATES)

    reviewed = []
    for path in candidates:
        path = path.expanduser()
        reviewed.append(str(path))
        if path.is_file():
            return path

    raise FileNotFoundError(
        "No se encontró Estructura_IIP.xlsx dentro del contenedor. "
        f"Rutas revisadas: {reviewed}"
    )


def read_sheet(excel: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    if sheet_name not in excel.sheet_names:
        raise ValueError(
            f"No existe la hoja {sheet_name!r}. Hojas: {excel.sheet_names}"
        )
    df = pd.read_excel(excel, sheet_name=sheet_name, dtype=object)
    df.columns = [str(column).strip() for column in df.columns]
    return df


def map_field_type(data_type: str) -> str:
    token = normalize_token(data_type)
    field_type = DATA_TYPE_TO_FIELD_TYPE.get(token)
    if field_type is None:
        raise ValueError(
            f"Tipo_dato sin mapeo: {data_type!r} (normalizado={token!r})."
        )
    return field_type


def is_required(data_type: str) -> bool:
    return normalize_token(data_type) != "texto_calculado"


# ---------------------------------------------------------------------------
# Lectura del instrumento
# ---------------------------------------------------------------------------


def load_structure(excel: pd.ExcelFile):
    """Obtiene preguntas principales y bucles desde las hojas anuales."""
    main_questions: dict[int, list[dict]] = {}
    loops: OrderedDict[str, dict] = OrderedDict()

    for year in ACTIVE_YEARS:
        df = read_sheet(excel, str(year))
        required = {"Pregunta", f"Pregunta {year}"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Faltan columnas en hoja {year}: {sorted(missing)}")

        questions = OrderedDict()
        for index, row in df.iterrows():
            raw_code = clean(row["Pregunta"])
            question_text = clean(row[f"Pregunta {year}"])
            if raw_code and question_text and raw_code not in questions:
                questions[raw_code] = {
                    "year": year,
                    "raw_code": raw_code,
                    "text": question_text,
                    "source_row": int(index) + 2,
                }
        main_questions[year] = list(questions.values())

        if year != 2023:
            continue

        loop_required = {
            "Bucle",
            "Bucle 2023",
            "Orden_subpregunta_bucle",
            "Subpregunta_bucle",
            "Pregunta",
        }
        missing = loop_required - set(df.columns)
        if missing:
            raise ValueError(f"Faltan columnas de bucle en 2023: {sorted(missing)}")

        for index, row in df.iterrows():
            loop_code = clean(row["Bucle"])
            loop_text = clean(row["Bucle 2023"])
            parent_code = clean(row["Pregunta"])
            sub_text = clean(row["Subpregunta_bucle"])
            order_value = row["Orden_subpregunta_bucle"]

            if not loop_code:
                continue
            if not loop_text or not parent_code:
                raise ValueError(
                    f"Bucle incompleto en hoja 2023, fila {int(index)+2}."
                )

            item = loops.setdefault(
                loop_code,
                {
                    "year": 2023,
                    "raw_code": loop_code,
                    "text": loop_text,
                    "parent_code": parent_code,
                    "source_row_first": int(index) + 2,
                    "subquestions": OrderedDict(),
                },
            )

            if normalize_text(item["text"]) != normalize_text(loop_text):
                raise ValueError(f"Textos contradictorios para {loop_code}.")
            if item["parent_code"] != parent_code:
                raise ValueError(f"Preguntas padre contradictorias para {loop_code}.")

            if sub_text:
                order = parse_integer(
                    order_value,
                    f"Orden_subpregunta_bucle de {loop_code}, fila {int(index)+2}",
                )
                previous = item["subquestions"].get(order)
                if previous and normalize_text(previous) != normalize_text(sub_text):
                    raise ValueError(
                        f"Orden {order} repetido con textos distintos en {loop_code}."
                    )
                item["subquestions"][order] = sub_text

    for loop_code, item in loops.items():
        orders = list(item["subquestions"])
        if orders != list(range(1, len(orders) + 1)):
            raise ValueError(f"Órdenes no consecutivos en {loop_code}: {orders}")
        item["subquestions"] = [
            {"order": order, "text": item["subquestions"][order]}
            for order in orders
        ]

    return main_questions, loops


def load_response_groups(excel: pd.ExcelFile):
    """Agrupa las filas de respuesta por pregunta y Texto_subpregunta."""
    by_year: dict[int, OrderedDict[str, list[dict]]] = {}

    for year in ACTIVE_YEARS:
        sheet_name = f"Respuestas_{year}"
        df = read_sheet(excel, sheet_name)

        required = {
            "Pregunta",
            "Texto_pregunta",
            "Tipo_pregunta",
            "Tipo_dato",
            "Orden_opcion",
            "Texto_opcion",
            "Valor_maximo",
        }
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Faltan columnas en {sheet_name}: {sorted(missing)}")

        has_subquestion = "Texto_subpregunta" in df.columns
        grouped: OrderedDict[str, list[dict]] = OrderedDict()

        for index, row in df.iterrows():
            question_code = clean(row["Pregunta"])
            question_text = clean(row["Texto_pregunta"])
            data_type = clean(row["Tipo_dato"])
            question_type = clean(row["Tipo_pregunta"])

            if not question_code or not question_text or not data_type:
                continue

            grouped.setdefault(question_code, []).append(
                {
                    "source_sheet": sheet_name,
                    "source_row": int(index) + 2,
                    "question_code": question_code,
                    "question_text": question_text,
                    "subquestion_text": (
                        clean(row["Texto_subpregunta"]) if has_subquestion else None
                    ),
                    "question_type": question_type,
                    "data_type": data_type,
                    "option_order": clean(row["Orden_opcion"]),
                    "option_text": clean(row["Texto_opcion"]),
                    "maximum_value": clean(row["Valor_maximo"]),
                }
            )

        by_year[year] = grouped

    return by_year


def group_rows_by_subquestion(rows: list[dict]) -> list[dict]:
    grouped: OrderedDict[str | None, dict] = OrderedDict()
    for row in rows:
        key = normalize_text(row["subquestion_text"])
        item = grouped.setdefault(
            key,
            {
                "subquestion_text": row["subquestion_text"],
                "rows": [],
                "source_row_first": row["source_row"],
            },
        )
        item["rows"].append(row)
    return list(grouped.values())


def choose_definition(group: dict) -> dict:
    """Valida que un grupo de opciones describa un único field."""
    rows = group["rows"]
    data_types = unique_in_order(row["data_type"] for row in rows)
    question_types = unique_in_order(row["question_type"] for row in rows)

    if len(data_types) != 1:
        raise ValueError(
            f"Una misma subpregunta tiene varios Tipo_dato: {data_types}. "
            f"Fila inicial: {group['source_row_first']}"
        )

    return {
        "subquestion_text": group["subquestion_text"],
        "question_text": rows[0]["question_text"],
        "data_type": data_types[0],
        "question_type": question_types[0] if question_types else None,
        "rows": rows,
        "source_sheet": rows[0]["source_sheet"],
        "source_row_first": group["source_row_first"],
    }


def special_2021_21_1(question: dict, rows: list[dict]) -> list[dict]:
    """Descompone entero_texto en NUMERIC + TEXT."""
    if len(rows) < 2:
        raise ValueError("Pregunta 21.1 de 2021 no contiene sus dos filas esperadas.")
    return [
        {
            "label": "Cantidad de innovaciones diseñadas",
            "description": question["text"],
            "data_type": "entero",
            "question_type": "Abierta numérica",
            "source_sheet": rows[0]["source_sheet"],
            "source_row_first": rows[0]["source_row"],
        },
        {
            "label": "Nombres de las innovaciones diseñadas",
            "description": "Indique los nombres de las innovaciones diseñadas.",
            "data_type": "texto",
            "question_type": "Abierta texto",
            "source_sheet": rows[1]["source_sheet"],
            "source_row_first": rows[1]["source_row"],
        },
    ]


def match_loop_response_groups(loop_code: str, loop: dict, response_rows: list[dict]):
    """Relaciona Subpregunta_bucle con Respuestas_2023.

    Se usa el orden de primera aparición como respaldo porque hay diferencias
    menores de redacción entre la hoja 2023 y Respuestas_2023.
    """
    groups = [
        choose_definition(group)
        for group in group_rows_by_subquestion(response_rows)
        if group["subquestion_text"] is not None
    ]

    # Pregunta 24.1 contiene una selección múltiple auxiliar que no pertenece
    # a los cinco campos de su tarjeta. Se mueve al grupo directo de Pregunta 24.
    if loop_code == "Pregunta 24.1":
        groups = [
            group
            for group in groups
            if not normalize_text(group["subquestion_text"]).startswith(
                "pregunta 24.1."
            )
        ]

    expected = loop["subquestions"]
    if len(groups) != len(expected):
        raise ValueError(
            f"{loop_code}: la hoja 2023 define {len(expected)} subpreguntas, "
            f"pero Respuestas_2023 contiene {len(groups)} grupos utilizables."
        )

    result = []
    for structure_subquestion, response_group in zip(expected, groups):
        result.append(
            {
                **response_group,
                "order": structure_subquestion["order"],
                "label": structure_subquestion["text"],
                "description": response_group["subquestion_text"],
            }
        )
    return result


def build_field_specs(main_questions, loops, responses):
    specs = []
    main_codes = {
        year: {item["raw_code"] for item in items}
        for year, items in main_questions.items()
    }
    loop_codes = set(loops)

    # 2019 y 2021: un field por pregunta, salvo entero_texto de 2021.
    for year in (2019, 2021):
        questions_by_code = {
            item["raw_code"]: item for item in main_questions[year]
        }
        for question_code in [item["raw_code"] for item in main_questions[year]]:
            rows = responses[year].get(question_code)
            if not rows:
                raise ValueError(
                    f"{question_code} de {year} no aparece en Respuestas_{year}."
                )
            question = questions_by_code[question_code]
            data_types = unique_in_order(row["data_type"] for row in rows)

            if year == 2021 and question_code == "Pregunta 21.1":
                definitions = special_2021_21_1(question, rows)
            else:
                if len(data_types) != 1:
                    raise ValueError(
                        f"{question_code} de {year} tiene varios Tipo_dato: {data_types}"
                    )
                definitions = [
                    {
                        "label": question["text"],
                        "description": question["text"],
                        "data_type": data_types[0],
                        "question_type": rows[0]["question_type"],
                        "source_sheet": rows[0]["source_sheet"],
                        "source_row_first": rows[0]["source_row"],
                    }
                ]

            for order, definition in enumerate(definitions, start=1):
                specs.append(
                    {
                        "year": year,
                        "question_code": question_code,
                        "response_question_code": question_code,
                        "group_kind": "DIRECT",
                        "display_order": order,
                        **definition,
                    }
                )

    # 2023: campos directos de preguntas principales.
    questions_2023 = {
        item["raw_code"]: item for item in main_questions[2023]
    }
    for question_code in [item["raw_code"] for item in main_questions[2023]]:
        rows = responses[2023].get(question_code)
        if not rows:
            raise ValueError(
                f"{question_code} no aparece en Respuestas_2023."
            )
        groups = [choose_definition(group) for group in group_rows_by_subquestion(rows)]

        # Pregunta 28.1 es mixta: solo el grupo sin Texto_subpregunta es directo.
        if question_code in loop_codes:
            groups = [group for group in groups if group["subquestion_text"] is None]

        for order, group in enumerate(groups, start=1):
            label = group["subquestion_text"] or questions_2023[question_code]["text"]
            specs.append(
                {
                    "year": 2023,
                    "question_code": question_code,
                    "response_question_code": question_code,
                    "group_kind": "DIRECT",
                    "display_order": order,
                    "label": label,
                    "description": group["subquestion_text"] or group["question_text"],
                    "data_type": group["data_type"],
                    "question_type": group["question_type"],
                    "source_sheet": group["source_sheet"],
                    "source_row_first": group["source_row_first"],
                }
            )

    # Selector auxiliar de Pregunta 24.1: pertenece al grupo directo de Pregunta 24.
    p241_rows = responses[2023].get("Pregunta 24.1", [])
    auxiliary_groups = [
        choose_definition(group)
        for group in group_rows_by_subquestion(p241_rows)
        if group["subquestion_text"] is not None
        and normalize_text(group["subquestion_text"]).startswith("pregunta 24.1.")
    ]
    if len(auxiliary_groups) != 1:
        raise ValueError(
            "Se esperaba exactamente una selección múltiple auxiliar en Pregunta 24.1."
        )
    auxiliary = auxiliary_groups[0]
    specs.append(
        {
            "year": 2023,
            "question_code": "Pregunta 24",
            "response_question_code": "Pregunta 24.1",
            "group_kind": "DIRECT",
            "display_order": 2,
            "label": auxiliary["subquestion_text"],
            "description": auxiliary["subquestion_text"],
            "data_type": auxiliary["data_type"],
            "question_type": auxiliary["question_type"],
            "source_sheet": auxiliary["source_sheet"],
            "source_row_first": auxiliary["source_row_first"],
        }
    )

    # 2023: campos repetibles de cada bucle.
    for loop_code, loop in loops.items():
        response_rows = responses[2023].get(loop_code)
        if not response_rows:
            raise ValueError(f"{loop_code} no aparece en Respuestas_2023.")

        definitions = match_loop_response_groups(loop_code, loop, response_rows)
        for definition in definitions:
            specs.append(
                {
                    "year": 2023,
                    "question_code": loop_code,
                    "response_question_code": loop_code,
                    "group_kind": "CARD",
                    "display_order": definition["order"],
                    "label": definition["label"],
                    "description": definition["description"],
                    "data_type": definition["data_type"],
                    "question_type": definition["question_type"],
                    "source_sheet": definition["source_sheet"],
                    "source_row_first": definition["source_row_first"],
                }
            )

    # Validaciones conocidas del archivo entregado.
    expected_counts = {
        (2019, "DIRECT"): 43,
        (2021, "DIRECT"): 53,
        (2023, "DIRECT"): 48,
        (2023, "CARD"): 101,
    }
    actual_counts = defaultdict(int)
    for spec in specs:
        actual_counts[(spec["year"], spec["group_kind"])] += 1
        spec["field_type_label"] = map_field_type(spec["data_type"])
        spec["required"] = is_required(spec["data_type"])

    if dict(actual_counts) != expected_counts:
        raise ValueError(
            f"Conteos de fields inesperados. Esperado={expected_counts}; "
            f"obtenido={dict(actual_counts)}"
        )

    return specs


# ---------------------------------------------------------------------------
# PostgreSQL: metadatos y estructuras previas
# ---------------------------------------------------------------------------


async def table_columns(conn, schema: str, table: str):
    result = await conn.execute(
        text(
            """
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_schema=:schema AND table_name=:table
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


async def ensure_field_types(conn):
    result = await conn.execute(
        text("SELECT UPPER(TRIM(label)) label, id::text id FROM reference.field_types")
    )
    grouped = defaultdict(list)
    for row in result.mappings().all():
        grouped[row["label"]].append(row["id"])

    for label, ids in grouped.items():
        if len(ids) > 1:
            raise ValueError(f"field_type duplicado para {label}: {ids}")

    for label, description in FIELD_TYPE_DESCRIPTIONS.items():
        if label in grouped:
            continue
        field_type_id = new_uuidv7()
        await conn.execute(
            text(
                """
                INSERT INTO reference.field_types (id, label, description)
                VALUES (CAST(:id AS uuid), :label, :description);
                """
            ),
            {"id": field_type_id, "label": label, "description": description},
        )
        grouped[label] = [field_type_id]
        logger.info(f"Creado reference.field_types: {label}")

    lookup = {label: ids[0] for label, ids in grouped.items()}
    required = set(FIELD_TYPE_DESCRIPTIONS)
    missing = required - set(lookup)
    if missing:
        raise ValueError(f"No fue posible crear field_types: {sorted(missing)}")
    return lookup


async def load_forms(conn):
    result = await conn.execute(
        text(
            "SELECT anno, id::text id FROM forms.forms WHERE anno IN (2019,2021,2023)"
        )
    )
    grouped = defaultdict(list)
    for row in result.mappings().all():
        grouped[int(row["anno"])].append(row["id"])

    lookup = {}
    for year in ACTIVE_YEARS:
        ids = grouped.get(year, [])
        if len(ids) != 1:
            raise ValueError(
                f"Debe existir exactamente un forms.forms para {year}; encontrados={ids}"
            )
        if not is_uuidv7(ids[0]):
            raise ValueError(f"form_id de {year} no es UUIDv7: {ids[0]}")
        lookup[year] = ids[0]
    return lookup


async def load_questions(conn, main_questions, loops):
    """Relaciona preguntas exclusivamente por año + label visible."""
    result = await conn.execute(
        text(
            """
            SELECT q.id::text question_id, q.form_id::text form_id,
                   q.label, q.description, q.is_loop, f.anno
            FROM forms.questions q
            JOIN forms.forms f ON f.id=q.form_id
            WHERE f.anno IN (2019,2021,2023)
            ORDER BY f.anno, q.display_order, q.id;
            """
        )
    )

    by_key = defaultdict(list)
    for row in result.mappings().all():
        by_key[(int(row["anno"]), normalize_text(row["label"]))].append(dict(row))

    expected_codes = []
    for year, questions in main_questions.items():
        expected_codes.extend((year, item["raw_code"]) for item in questions)
    expected_codes.extend((2023, code) for code in loops)

    lookup = {}
    for year, code in expected_codes:
        key = (year, normalize_text(code))
        rows = by_key.get(key, [])
        if len(rows) != 1:
            raise ValueError(
                f"No se pudo resolver forms.questions para {year} / {code}. "
                f"Coincidencias={len(rows)}. Ejecuta/corrige 11d y 11e antes de 11h."
            )
        if not is_uuidv7(rows[0]["question_id"]):
            raise ValueError(
                f"question_id de {year}/{code} no es UUIDv7: "
                f"{rows[0]["question_id"]}"
            )
        lookup[(year, code)] = rows[0]

    return lookup


async def ensure_loop_flags(conn, questions, loops):
    """Asegura que las 27 preguntas repetibles de 2023 tengan is_loop=TRUE."""
    for loop_code in loops:
        question_id = questions[(2023, loop_code)]["question_id"]
        await conn.execute(
            text(
                """
                UPDATE forms.questions
                SET is_loop=TRUE, updated_at=NOW()
                WHERE id=CAST(:id AS uuid);
                """
            ),
            {"id": question_id},
        )


async def ensure_card_templates(conn, questions, loops):
    columns = await table_columns(conn, "forms", "card_templates")
    result = await conn.execute(
        text(
            """
            SELECT id::text id, question_id::text question_id, label
            FROM forms.card_templates;
            """
        )
    )
    by_question = defaultdict(list)
    for row in result.mappings().all():
        by_question[row["question_id"]].append(dict(row))

    lookup = {}
    for loop_code, loop in loops.items():
        question = questions[(2023, loop_code)]
        question_id = question["question_id"]
        existing = by_question.get(question_id, [])
        if len(existing) > 1:
            raise ValueError(
                f"La pregunta {loop_code} tiene varios card_templates: "
                f"{[row['id'] for row in existing]}"
            )

        label = truncate(f"Tarjeta - {loop_code}", columns["label"]["max_length"])
        description = truncate(loop["text"], columns["description"]["max_length"])
        helper = json.dumps(
            {
                "source": SOURCE_NAME,
                "entity": "forms.card_templates",
                "year": 2023,
                "question_code": loop_code,
                "parent_question_code": loop["parent_code"],
                "subquestion_count": len(loop["subquestions"]),
            },
            ensure_ascii=False,
            sort_keys=True,
        )

        if existing:
            card_id = existing[0]["id"]
            await conn.execute(
                text(
                    """
                    UPDATE forms.card_templates
                    SET label=:label, description=:description, helper=:helper,
                        updated_at=NOW()
                    WHERE id=CAST(:id AS uuid);
                    """
                ),
                {
                    "id": card_id,
                    "label": label,
                    "description": description,
                    "helper": helper,
                },
            )
        else:
            card_id = new_uuidv7()
            await conn.execute(
                text(
                    """
                    INSERT INTO forms.card_templates
                        (id, question_id, label, description, helper, updated_at)
                    VALUES
                        (CAST(:id AS uuid), CAST(:question_id AS uuid),
                         :label, :description, :helper, NOW());
                    """
                ),
                {
                    "id": card_id,
                    "question_id": question_id,
                    "label": label,
                    "description": description,
                    "helper": helper,
                },
            )
        lookup[loop_code] = card_id

    return lookup


async def ensure_field_groups(conn, forms, questions, main_questions, loops, cards):
    columns = await table_columns(conn, "forms", "field_groups")
    result = await conn.execute(
        text(
            """
            SELECT id::text id, form_id::text form_id,
                   question_id::text question_id,
                   card_template_id::text card_template_id,
                   display_order
            FROM forms.field_groups;
            """
        )
    )
    direct_existing = defaultdict(list)
    card_existing = defaultdict(list)
    for row in result.mappings().all():
        row = dict(row)
        if row["card_template_id"] is None:
            direct_existing[row["question_id"]].append(row)
        else:
            card_existing[(row["question_id"], row["card_template_id"])].append(row)

    direct_lookup = {}
    for year, items in main_questions.items():
        for item in items:
            code = item["raw_code"]
            question = questions[(year, code)]
            qid = question["question_id"]
            existing = direct_existing.get(qid, [])
            if len(existing) > 1:
                raise ValueError(f"Más de un field_group directo para {year}/{code}.")

            label = truncate(f"Respuesta - {code}", columns["label"]["max_length"])
            description = truncate(item["text"], columns["description"]["max_length"])

            if existing:
                group_id = existing[0]["id"]
                await conn.execute(
                    text(
                        """
                        UPDATE forms.field_groups
                        SET form_id=CAST(:form_id AS uuid), label=:label,
                            description=:description, display_order=1,
                            updated_at=NOW()
                        WHERE id=CAST(:id AS uuid);
                        """
                    ),
                    {
                        "id": group_id,
                        "form_id": forms[year],
                        "label": label,
                        "description": description,
                    },
                )
            else:
                group_id = new_uuidv7()
                await conn.execute(
                    text(
                        """
                        INSERT INTO forms.field_groups
                            (id, form_id, question_id, card_template_id,
                             label, description, display_order, updated_at)
                        VALUES
                            (CAST(:id AS uuid), CAST(:form_id AS uuid),
                             CAST(:question_id AS uuid), NULL,
                             :label, :description, 1, NOW());
                        """
                    ),
                    {
                        "id": group_id,
                        "form_id": forms[year],
                        "question_id": qid,
                        "label": label,
                        "description": description,
                    },
                )
            direct_lookup[(year, code)] = group_id

    card_lookup = {}
    for loop_code, loop in loops.items():
        question = questions[(2023, loop_code)]
        qid = question["question_id"]
        card_id = cards[loop_code]
        existing = card_existing.get((qid, card_id), [])
        if len(existing) > 1:
            raise ValueError(f"Más de un field_group CARD para {loop_code}.")

        label = truncate(f"Detalle repetible - {loop_code}", columns["label"]["max_length"])
        description = truncate(loop["text"], columns["description"]["max_length"])

        if existing:
            group_id = existing[0]["id"]
            await conn.execute(
                text(
                    """
                    UPDATE forms.field_groups
                    SET form_id=CAST(:form_id AS uuid), label=:label,
                        description=:description, display_order=2,
                        updated_at=NOW()
                    WHERE id=CAST(:id AS uuid);
                    """
                ),
                {
                    "id": group_id,
                    "form_id": forms[2023],
                    "label": label,
                    "description": description,
                },
            )
        else:
            group_id = new_uuidv7()
            await conn.execute(
                text(
                    """
                    INSERT INTO forms.field_groups
                        (id, form_id, question_id, card_template_id,
                         label, description, display_order, updated_at)
                    VALUES
                        (CAST(:id AS uuid), CAST(:form_id AS uuid),
                         CAST(:question_id AS uuid), CAST(:card_template_id AS uuid),
                         :label, :description, 2, NOW());
                    """
                ),
                {
                    "id": group_id,
                    "form_id": forms[2023],
                    "question_id": qid,
                    "card_template_id": card_id,
                    "label": label,
                    "description": description,
                },
            )
        card_lookup[loop_code] = group_id

    return direct_lookup, card_lookup


# ---------------------------------------------------------------------------
# Inserción de fields
# ---------------------------------------------------------------------------


async def load_existing_fields(conn):
    result = await conn.execute(
        text(
            """
            SELECT id::text id, form_id::text form_id,
                   field_group_id::text field_group_id,
                   field_type_id::text field_type_id,
                   label, description, required, display_order
            FROM forms.fields;
            """
        )
    )
    by_key = defaultdict(list)
    for row in result.mappings().all():
        row = dict(row)
        by_key[(row["field_group_id"], int(row["display_order"]))].append(row)
    return by_key


async def save_fields(conn, specs, forms, direct_groups, card_groups, field_types):
    columns = await table_columns(conn, "forms", "fields")
    required_columns = {
        "id", "form_id", "field_group_id", "field_type_id", "label",
        "description", "required", "display_order", "updated_at",
    }
    missing = required_columns - set(columns)
    if missing:
        raise ValueError(f"Faltan columnas en forms.fields: {sorted(missing)}")

    existing_by_key = await load_existing_fields(conn)
    inserted = 0
    updated = 0

    for spec in specs:
        group_id = (
            direct_groups[(spec["year"], spec["question_code"])]
            if spec["group_kind"] == "DIRECT"
            else card_groups[spec["question_code"]]
        )
        key = (group_id, int(spec["display_order"]))
        existing = existing_by_key.get(key, [])
        if len(existing) > 1:
            raise ValueError(f"Fields duplicados para grupo/orden {key}.")

        field_id = existing[0]["id"] if existing else new_uuidv7()
        label = truncate(spec["label"], columns["label"]["max_length"])
        description = truncate(
            (
                f"{spec['description']}\n"
                f"Fuente: {spec['source_sheet']}, fila {spec['source_row_first']}. "
                f"Tipo de pregunta: {spec['question_type'] or 'sin especificar'}."
            ),
            columns["description"]["max_length"],
        )
        params = {
            "id": field_id,
            "form_id": forms[spec["year"]],
            "field_group_id": group_id,
            "field_type_id": field_types[spec["field_type_label"]],
            "label": label,
            "description": description,
            "required": bool(spec["required"]),
            "display_order": int(spec["display_order"]),
        }

        if existing:
            await conn.execute(
                text(
                    """
                    UPDATE forms.fields
                    SET form_id=CAST(:form_id AS uuid),
                        field_group_id=CAST(:field_group_id AS uuid),
                        field_type_id=CAST(:field_type_id AS uuid),
                        label=:label, description=:description,
                        required=:required, display_order=:display_order,
                        updated_at=NOW()
                    WHERE id=CAST(:id AS uuid);
                    """
                ),
                params,
            )
            updated += 1
        else:
            await conn.execute(
                text(
                    """
                    INSERT INTO forms.fields
                        (id, form_id, field_group_id, field_type_id,
                         label, description, required, display_order, updated_at)
                    VALUES
                        (CAST(:id AS uuid), CAST(:form_id AS uuid),
                         CAST(:field_group_id AS uuid), CAST(:field_type_id AS uuid),
                         :label, :description, :required, :display_order, NOW());
                    """
                ),
                params,
            )
            inserted += 1

    return inserted, updated


async def validate_fields(conn, expected_total: int):
    result = await conn.execute(
        text(
            """
            SELECT f.anno,
                   COUNT(*) total,
                   COUNT(*) FILTER (WHERE fg.card_template_id IS NULL) directos,
                   COUNT(*) FILTER (WHERE fg.card_template_id IS NOT NULL) repetibles
            FROM forms.fields fld
            JOIN forms.field_groups fg ON fg.id=fld.field_group_id
            JOIN forms.forms f ON f.id=fld.form_id
            WHERE f.anno IN (2019,2021,2023)
            GROUP BY f.anno ORDER BY f.anno;
            """
        )
    )
    actual = {
        int(row["anno"]): (
            int(row["total"]), int(row["directos"]), int(row["repetibles"])
        )
        for row in result.mappings().all()
    }
    expected = {
        2019: (43, 43, 0),
        2021: (53, 53, 0),
        2023: (149, 48, 101),
    }
    if actual != expected:
        raise ValueError(
            f"Validación de forms.fields falló. Esperado={expected}; obtenido={actual}"
        )
    if sum(value[0] for value in actual.values()) != expected_total:
        raise ValueError("El total validado no coincide con los fields esperados.")


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------


async def upgrade(gh=None, api=None) -> None:
    del gh, api
    path = resolve_excel_path()
    logger.info(f"[11h] Archivo: {path}")
    print(f"[11h] Archivo Excel: {path}", flush=True)

    excel = pd.ExcelFile(path)
    main_questions, loops = load_structure(excel)
    responses = load_response_groups(excel)
    specs = build_field_specs(main_questions, loops, responses)

    print(
        "[11h] Especificaciones construidas: "
        f"2019=43, 2021=53, 2023-directos=48, 2023-repetibles=101, "
        f"total={len(specs)}",
        flush=True,
    )

    async with async_engine.begin() as conn:
        forms = await load_forms(conn)
        questions = await load_questions(conn, main_questions, loops)
        field_types = await ensure_field_types(conn)
        await ensure_loop_flags(conn, questions, loops)
        cards = await ensure_card_templates(conn, questions, loops)
        direct_groups, card_groups = await ensure_field_groups(
            conn, forms, questions, main_questions, loops, cards
        )
        inserted, updated = await save_fields(
            conn, specs, forms, direct_groups, card_groups, field_types
        )
        await validate_fields(conn, len(specs))

    logger.info(
        f"[11h] forms.fields completado. Insertados={inserted}; actualizados={updated}."
    )
    print(
        f"[11h] OK. Insertados={inserted}; actualizados={updated}; total=245.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
