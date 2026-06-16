"""Puebla las preguntas tipo bucle de 2023 en forms.questions.

Dependencias previas:
    11c_seed_sections.py
    11d_seed_questions.py

Fuente:
    Estructura_IIP.xlsx

Hojas:
    2023
    Respuestas_2023

Modelo aplicado:
- Los bucles independientes se crean como nuevas filas de forms.questions con
  is_main_question=False e is_loop=True.
- La Pregunta 28.1 es una pregunta mixta: ya existe como pregunta principal y
  también contiene una estructura repetible. No se duplica. Se conserva su UUID,
  se mantiene is_main_question=True y se confirma is_loop=True.
- La definición completa del bucle se almacena en helper.loop_definition para que
  los pobladores posteriores puedan crear card_templates, field_groups y fields.
- Los registros nuevos usan UUID versión 7.
- Las ejecuciones posteriores conservan los UUID existentes.
"""

import json
import math
import os
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from uuid_utils import uuid7

from shared_db import async_engine
from shared_utils.logger import get_logger


logger = get_logger("pop/loop_questions")

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

YEAR = 2023
SOURCE = "Estructura_IIP.xlsx"
VALID_SOURCES = {
    "Estructura IIP.xlsx",
    "Estructura_IIP.xlsx",
}
EXPECTED_LOOP_COUNT = int(os.getenv("IIP_EXPECTED_2023_LOOP_COUNT", "27"))
EXPECTED_MIXED_LOOP_COUNT = int(
    os.getenv("IIP_EXPECTED_2023_MIXED_LOOP_COUNT", "1")
)


# ---------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------


def clean(value):
    """Convierte valores vacíos y NaN en None."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    value = str(value).strip()
    return value or None


def norm(value):
    """Normaliza texto para cruces robustos."""
    value = clean(value)

    if value is None:
        return None

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )
    value = re.sub(r"\s+", " ", value.lower())

    return value.strip()


def number(value):
    """Convierte valores numéricos del Excel a float."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, bool):
        raise ValueError(f"No se puede convertir un booleano a número: {value}")

    if isinstance(value, (int, float)):
        numeric = float(value)
        return None if math.isnan(numeric) else numeric

    value = clean(value)

    if value is None:
        return None

    value = (
        value.replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Valor numérico inválido: {value!r}") from exc


def positive_int(value, source_row: int) -> int:
    """Valida el orden de una subpregunta de bucle."""
    numeric = number(value)

    if numeric is None or not numeric.is_integer() or numeric <= 0:
        raise ValueError(
            "Orden_subpregunta_bucle inválido en fila "
            f"{source_row}: {value!r}"
        )

    return int(numeric)


def same_number(left, right, tolerance: float = 1e-9) -> bool:
    """Compara ponderaciones con tolerancia decimal."""
    if left is None and right is None:
        return True

    if left is None or right is None:
        return False

    return math.isclose(
        float(left),
        float(right),
        rel_tol=tolerance,
        abs_tol=tolerance,
    )


def suffix(value):
    """Extrae la numeración completa de un código."""
    value = clean(value)

    if value is None:
        return None

    match = re.search(r"(\d+(?:[.,]\d+)*)", value)

    if not match:
        return None

    return (
        match.group(1)
        .replace(".", "_")
        .replace(",", "_")
    )


def code(prefix: str, value) -> str:
    """Construye un código técnico estable."""
    code_suffix = suffix(value)

    if code_suffix:
        return f"{prefix}{code_suffix}"

    normalized = norm(value) or "sin_codigo"
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")

    return f"{prefix}{normalized}"


def sort_code(value):
    """Construye una llave ordenable a partir del código visible."""
    code_suffix = suffix(value)

    if code_suffix is None:
        return (10**9,)

    return tuple(
        int(part)
        for part in code_suffix.split("_")
        if part.isdigit()
    )


def uuid7_ok(value) -> bool:
    """Valida UUID versión 7."""
    try:
        return UUID(str(value)).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def helper_dict(value):
    """Convierte helper JSON a diccionario."""
    value = clean(value)

    if value is None:
        return None

    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None

    return parsed if isinstance(parsed, dict) else None


def unique(values) -> list:
    """Obtiene valores únicos conservando el orden."""
    output = []
    seen = set()

    for value in values:
        value = clean(value)

        if value is None:
            continue

        normalized = norm(value)

        if normalized in seen:
            continue

        seen.add(normalized)
        output.append(value)

    return output


def read_sheet(excel: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    """Lee una hoja obligatoria del archivo."""
    if sheet_name not in excel.sheet_names:
        raise ValueError(
            f"No existe la hoja {sheet_name!r}. "
            f"Hojas disponibles: {excel.sheet_names}"
        )

    df = pd.read_excel(excel, sheet_name=sheet_name, dtype=object)
    df.columns = [str(column).strip() for column in df.columns]

    return df


# ---------------------------------------------------------------------
# LECTURA DE BUCLES DESDE LA HOJA 2023
# ---------------------------------------------------------------------


def load_loop_records(excel: pd.ExcelFile) -> list[dict]:
    """Construye las 27 definiciones únicas de bucle de 2023."""
    df = read_sheet(excel, "2023")

    required = {
        "Componente",
        "Componente 2023",
        "Variable",
        "Variable 2023",
        "Indicador",
        "Indicador 2023",
        "Pregunta",
        "Pregunta 2023",
        "Maxp",
        "Bucle",
        "Bucle 2023",
        "Maxb",
        "Orden_subpregunta_bucle",
        "Subpregunta_bucle",
        "Max_subpregunta_bucle",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas en la hoja 2023: {sorted(missing)}"
        )

    data = pd.DataFrame(
        {
            "source_row": df.index + 2,
            "component_raw": df["Componente"],
            "component_label": df["Componente 2023"],
            "variable_raw": df["Variable"],
            "variable_label": df["Variable 2023"],
            "indicator_raw": df["Indicador"],
            "indicator_label": df["Indicador 2023"],
            "parent_raw": df["Pregunta"],
            "parent_text": df["Pregunta 2023"],
            "parent_weight": df["Maxp"],
            "loop_raw": df["Bucle"],
            "loop_text": df["Bucle 2023"],
            "loop_weight": df["Maxb"],
            "subquestion_order": df["Orden_subpregunta_bucle"],
            "subquestion_text": df["Subpregunta_bucle"],
            "subquestion_weight": df["Max_subpregunta_bucle"],
        }
    )

    for column in data.columns:
        if column != "source_row":
            data[column] = data[column].apply(clean)

    # Soporta celdas combinadas o valores jerárquicos no repetidos.
    fill_columns = [
        "component_raw",
        "component_label",
        "variable_raw",
        "variable_label",
        "indicator_raw",
        "indicator_label",
        "parent_raw",
        "parent_text",
        "parent_weight",
    ]
    data[fill_columns] = data[fill_columns].ffill()

    data = data[
        data["component_raw"].notna()
        & data["component_label"].notna()
        & data["variable_raw"].notna()
        & data["variable_label"].notna()
        & data["indicator_raw"].notna()
        & data["indicator_label"].notna()
        & data["parent_raw"].notna()
        & data["parent_text"].notna()
        & data["loop_raw"].notna()
        & data["loop_text"].notna()
        & data["subquestion_text"].notna()
    ].copy()

    registry = OrderedDict()

    for _, row in data.iterrows():
        source_row = int(row["source_row"])

        component_code = code("C", row["component_raw"])
        variable_code = (
            f"{component_code}_{code('V', row['variable_raw'])}"
        )
        indicator_code = (
            f"{variable_code}_{code('I', row['indicator_raw'])}"
        )
        parent_question_code = code("P", row["parent_raw"])
        loop_question_code = code("P", row["loop_raw"])

        key = (
            YEAR,
            indicator_code,
            loop_question_code,
        )

        candidate = {
            "year": YEAR,
            "source_sheet": "2023",
            "source_row_first": source_row,
            "source_row_last": source_row,
            "source_occurrences": 1,
            "component_code": component_code,
            "variable_code": variable_code,
            "indicator_code": indicator_code,
            "component_label": row["component_label"],
            "variable_label": row["variable_label"],
            "indicator_label": row["indicator_label"],
            "parent_question_code": parent_question_code,
            "parent_question_raw_code": row["parent_raw"],
            "parent_question_text": row["parent_text"],
            "parent_question_weight": number(row["parent_weight"]),
            "loop_question_code": loop_question_code,
            "loop_raw_code": row["loop_raw"],
            "loop_text": row["loop_text"],
            "loop_weight": number(row["loop_weight"]),
            "is_mixed_question": (
                parent_question_code == loop_question_code
            ),
            "indicator_fallback_key": (
                YEAR,
                norm(row["component_label"]),
                norm(row["variable_label"]),
                norm(row["indicator_label"]),
            ),
            "subquestions": OrderedDict(),
        }

        current = registry.get(key)

        if current is None:
            registry[key] = candidate
            current = candidate
        else:
            checks = [
                current["component_code"] == candidate["component_code"],
                current["variable_code"] == candidate["variable_code"],
                current["indicator_code"] == candidate["indicator_code"],
                current["parent_question_code"]
                == candidate["parent_question_code"],
                norm(current["loop_text"]) == norm(candidate["loop_text"]),
                same_number(
                    current["loop_weight"],
                    candidate["loop_weight"],
                ),
                current["is_mixed_question"]
                == candidate["is_mixed_question"],
            ]

            if not all(checks):
                raise ValueError(
                    f"Datos contradictorios para el bucle {key}, "
                    f"fila {source_row}."
                )

            current["source_row_last"] = source_row
            current["source_occurrences"] += 1

        subquestion_order = positive_int(
            row["subquestion_order"],
            source_row,
        )

        subquestion = {
            "order": subquestion_order,
            "text": row["subquestion_text"],
            "weight": number(row["subquestion_weight"]),
        }

        previous = current["subquestions"].get(subquestion_order)

        if previous is not None and (
            norm(previous["text"]) != norm(subquestion["text"])
            or not same_number(
                previous["weight"],
                subquestion["weight"],
            )
        ):
            raise ValueError(
                f"Orden {subquestion_order} repetido con información "
                f"diferente en {row['loop_raw']}."
            )

        current["subquestions"][subquestion_order] = subquestion

    records = list(registry.values())
    records.sort(
        key=lambda item: (
            sort_code(item["loop_raw_code"]),
            item["indicator_code"],
        )
    )

    for record in records:
        record["subquestions"] = [
            record["subquestions"][order]
            for order in sorted(record["subquestions"])
        ]

        orders = [
            subquestion["order"]
            for subquestion in record["subquestions"]
        ]

        if orders != list(range(1, len(orders) + 1)):
            raise ValueError(
                f"Órdenes no consecutivos en {record['loop_raw_code']}: "
                f"{orders}"
            )

        record["subquestion_count"] = len(orders)
        record["question_uid"] = (
            f"{YEAR}|{record['indicator_code']}|"
            f"{record['loop_question_code']}"
        )

    if len(records) != EXPECTED_LOOP_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_LOOP_COUNT} bucles únicos y se "
            f"encontraron {len(records)}."
        )

    mixed_count = sum(
        1
        for record in records
        if record["is_mixed_question"]
    )

    if mixed_count != EXPECTED_MIXED_LOOP_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_MIXED_LOOP_COUNT} bucles mixtos y se "
            f"encontraron {mixed_count}."
        )

    return records


# ---------------------------------------------------------------------
# METADATOS DE RESPUESTAS 2023
# ---------------------------------------------------------------------


def add_response_metadata(
    excel: pd.ExcelFile,
    records: list[dict],
) -> None:
    """Conecta cada bucle con sus metadatos de Respuestas_2023.

    Para la pregunta mixta 28.1, Texto_pregunta corresponde al enunciado de
    la pregunta principal, no al texto explicativo de la tarjeta repetible.
    Por eso ese único caso no exige igualdad entre ambos textos.
    """
    df = read_sheet(excel, "Respuestas_2023")

    required = {
        "Pregunta",
        "Texto_pregunta",
        "Texto_subpregunta",
        "Tipo_pregunta",
        "Tipo_dato",
        "Orden_opcion",
        "Texto_opcion",
        "Valor_maximo",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas en Respuestas_2023: {sorted(missing)}"
        )

    grouped = OrderedDict()

    for index, row in df.iterrows():
        raw_code = clean(row["Pregunta"])
        question_text = clean(row["Texto_pregunta"])

        if raw_code is None or question_text is None:
            continue

        grouped.setdefault(raw_code, []).append(
            {
                "source_row": int(index) + 2,
                "question_text": question_text,
                "subquestion_text": clean(row["Texto_subpregunta"]),
                "question_type": clean(row["Tipo_pregunta"]),
                "data_type": clean(row["Tipo_dato"]),
                "option_order": clean(row["Orden_opcion"]),
                "option_text": clean(row["Texto_opcion"]),
                "maximum_value": clean(row["Valor_maximo"]),
            }
        )

    for record in records:
        response_rows = grouped.get(record["loop_raw_code"])

        if not response_rows:
            raise ValueError(
                f"{record['loop_raw_code']} no aparece en Respuestas_2023."
            )

        response_texts = unique(
            item["question_text"]
            for item in response_rows
        )

        if len(response_texts) != 1:
            raise ValueError(
                f"Respuestas_2023 contiene textos diferentes para "
                f"{record['loop_raw_code']}: {response_texts}"
            )

        response_question_text = response_texts[0]
        text_matches_loop = (
            norm(response_question_text)
            == norm(record["loop_text"])
        )

        if not record["is_mixed_question"] and not text_matches_loop:
            raise ValueError(
                f"El texto de {record['loop_raw_code']} no coincide entre "
                "la hoja 2023 y Respuestas_2023."
            )

        response_subquestions = unique(
            item["subquestion_text"]
            for item in response_rows
        )

        structure_subquestions = [
            item["text"]
            for item in record["subquestions"]
        ]

        structure_normalized = {
            norm(value)
            for value in structure_subquestions
            if clean(value) is not None
        }
        response_normalized = {
            norm(value)
            for value in response_subquestions
            if clean(value) is not None
        }

        response_only_subquestions = [
            value
            for value in response_subquestions
            if norm(value) not in structure_normalized
        ]
        structure_only_subquestions = [
            value
            for value in structure_subquestions
            if norm(value) not in response_normalized
        ]

        record.update(
            {
                "response_sheet": "Respuestas_2023",
                "response_row_first": min(
                    item["source_row"]
                    for item in response_rows
                ),
                "response_row_last": max(
                    item["source_row"]
                    for item in response_rows
                ),
                "response_row_count": len(response_rows),
                "response_question_text": response_question_text,
                "response_text_matches_loop": text_matches_loop,
                "question_types": unique(
                    item["question_type"]
                    for item in response_rows
                ),
                "data_types": unique(
                    item["data_type"]
                    for item in response_rows
                ),
                "response_subquestions": response_subquestions,
                "response_subquestion_count": len(response_subquestions),
                "response_only_subquestions": response_only_subquestions,
                "structure_only_subquestions": structure_only_subquestions,
                "has_options": any(
                    item["option_text"] is not None
                    for item in response_rows
                ),
                "option_row_count": sum(
                    item["option_text"] is not None
                    for item in response_rows
                ),
                "has_maximum_values": any(
                    item["maximum_value"] is not None
                    for item in response_rows
                ),
                "maximum_value_row_count": sum(
                    item["maximum_value"] is not None
                    for item in response_rows
                ),
            }
        )


# ---------------------------------------------------------------------
# CONSULTAS A POSTGRESQL
# ---------------------------------------------------------------------


async def table_columns(conn) -> dict:
    """Consulta la estructura real de forms.questions."""
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'forms'
              AND table_name = 'questions'
            ORDER BY ordinal_position;
            """
        )
    )

    rows = result.mappings().all()

    if not rows:
        raise ValueError("No se encontró forms.questions en PostgreSQL.")

    columns = {
        row["column_name"]: {
            "max": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }

    required = {
        "id",
        "form_id",
        "section_id",
        "file_id",
        "label",
        "description",
        "helper",
        "display_order",
        "required",
        "is_loop",
        "updated_at",
    }

    missing = required - set(columns)

    if missing:
        raise ValueError(
            f"Faltan columnas en forms.questions: {sorted(missing)}"
        )

    return columns


async def form_id_2023(conn) -> str:
    """Obtiene el formulario único de 2023."""
    result = await conn.execute(
        text(
            """
            SELECT id::text AS id
            FROM forms.forms
            WHERE anno = :year;
            """
        ),
        {"year": YEAR},
    )

    rows = result.mappings().all()

    if len(rows) != 1:
        raise ValueError(
            f"Debe existir un único formulario {YEAR}; hay {len(rows)}."
        )

    form_id = rows[0]["id"]

    if not uuid7_ok(form_id):
        raise ValueError(f"El form_id de {YEAR} no es UUIDv7: {form_id}")

    return form_id


async def indicator_maps(conn) -> tuple[dict, dict]:
    """Construye búsquedas de indicadores por código y etiquetas."""
    result = await conn.execute(
        text(
            """
            SELECT
                component.label AS component_label,
                variable.label AS variable_label,
                indicator.label AS indicator_label,
                indicator.id::text AS indicator_id,
                indicator.helper
            FROM forms.sections indicator
            JOIN forms.section_types indicator_type
                ON indicator_type.id = indicator.section_type_id
               AND UPPER(TRIM(indicator_type.label)) = 'INDICADOR'
            JOIN forms.sections variable
                ON variable.id = indicator.parent_id
            JOIN forms.sections component
                ON component.id = variable.parent_id
            JOIN forms.forms form
                ON form.id = indicator.form_id
            WHERE form.anno = :year;
            """
        ),
        {"year": YEAR},
    )

    by_code = {}
    by_labels = {}

    for row in result.mappings().all():
        indicator_id = row["indicator_id"]

        if not uuid7_ok(indicator_id):
            raise ValueError(
                f"Indicador sin UUIDv7: {indicator_id}"
            )

        helper = helper_dict(row["helper"])

        if helper and helper.get("entity") == "forms.sections":
            indicator_code = clean(helper.get("code"))

            if indicator_code:
                key = (YEAR, indicator_code)

                if key in by_code and by_code[key] != indicator_id:
                    raise ValueError(
                        f"Indicador duplicado para {key}."
                    )

                by_code[key] = indicator_id

        label_key = (
            YEAR,
            norm(row["component_label"]),
            norm(row["variable_label"]),
            norm(row["indicator_label"]),
        )

        if label_key in by_labels and by_labels[label_key] != indicator_id:
            raise ValueError(
                f"Indicador ambiguo por etiquetas: {label_key}"
            )

        by_labels[label_key] = indicator_id

    return by_code, by_labels


async def main_question_map(conn) -> dict[tuple, dict]:
    """Obtiene todas las preguntas principales, incluida la mixta 28.1."""
    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                question.form_id::text AS form_id,
                question.section_id::text AS section_id,
                question.label,
                question.description,
                question.helper,
                question.display_order,
                question.required,
                question.is_loop,
                section.helper AS section_helper
            FROM forms.questions question
            JOIN forms.forms form
                ON form.id = question.form_id
            LEFT JOIN forms.sections section
                ON section.id = question.section_id
            WHERE form.anno = :year
            ORDER BY question.id;
            """
        ),
        {"year": YEAR},
    )

    output = {}

    for row in result.mappings().all():
        helper = helper_dict(row["helper"])

        if not helper:
            continue

        if helper.get("source") not in VALID_SOURCES:
            continue

        if helper.get("entity") != "forms.questions":
            continue

        if helper.get("is_main_question") is not True:
            continue

        section_helper = helper_dict(row["section_helper"]) or {}
        question_code = (
            clean(helper.get("question_code"))
            or code("P", row["label"])
        )
        indicator_code = (
            clean(helper.get("indicator_code"))
            or clean(section_helper.get("code"))
        )

        if indicator_code is None:
            raise ValueError(
                "No se pudo identificar indicator_code para la pregunta "
                f"principal {row['question_id']}."
            )

        key = (
            YEAR,
            indicator_code,
            question_code,
        )

        if key in output:
            raise ValueError(
                f"Pregunta principal duplicada: {key}"
            )

        if not uuid7_ok(row["question_id"]):
            raise ValueError(
                "Pregunta principal sin UUIDv7: "
                f"{row['question_id']}"
            )

        output[key] = {
            "question_id": row["question_id"],
            "form_id": row["form_id"],
            "section_id": row["section_id"],
            "label": row["label"],
            "description": row["description"],
            "helper": helper,
            "display_order": int(row["display_order"] or 0),
            "required": row["required"],
            "is_loop": row["is_loop"],
            "question_code": question_code,
            "indicator_code": indicator_code,
        }

    return output


async def existing_independent_loop_map(conn) -> dict[tuple, dict]:
    """Obtiene únicamente los bucles independientes ya creados."""
    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                question.label,
                question.helper,
                question.is_loop,
                section.helper AS section_helper
            FROM forms.questions question
            JOIN forms.forms form
                ON form.id = question.form_id
            LEFT JOIN forms.sections section
                ON section.id = question.section_id
            WHERE form.anno = :year
              AND question.is_loop = TRUE
            ORDER BY question.id;
            """
        ),
        {"year": YEAR},
    )

    output = {}

    for row in result.mappings().all():
        helper = helper_dict(row["helper"])

        if not helper or helper.get("source") not in VALID_SOURCES:
            continue

        if helper.get("entity") != "forms.questions":
            continue

        # La pregunta mixta es principal y no pertenece a este mapa.
        if helper.get("is_main_question") is True:
            continue

        section_helper = helper_dict(row["section_helper"]) or {}
        question_code = (
            clean(helper.get("question_code"))
            or code("P", row["label"])
        )
        indicator_code = (
            clean(helper.get("indicator_code"))
            or clean(section_helper.get("code"))
        )

        if indicator_code is None:
            raise ValueError(
                f"No se encontró indicator_code para {row['question_id']}."
            )

        key = (
            YEAR,
            indicator_code,
            question_code,
        )

        if key in output:
            raise ValueError(
                f"Bucle independiente duplicado: {key}"
            )

        if not uuid7_ok(row["question_id"]):
            raise ValueError(
                f"Bucle independiente sin UUIDv7: {row['question_id']}"
            )

        output[key] = {
            "question_id": row["question_id"],
            "helper": helper,
        }

    return output


# ---------------------------------------------------------------------
# CONSTRUCCIÓN DE HELPERS Y REGISTROS
# ---------------------------------------------------------------------


def make_loop_definition(
    record: dict,
    parent_question_id: str | None,
) -> dict:
    """Construye el contrato común utilizado por card_templates y fields."""
    return {
        "source_sheet": record["source_sheet"],
        "source_row_first": record["source_row_first"],
        "source_row_last": record["source_row_last"],
        "source_occurrences": record["source_occurrences"],
        "response_sheet": record["response_sheet"],
        "response_row_first": record["response_row_first"],
        "response_row_last": record["response_row_last"],
        "response_row_count": record["response_row_count"],
        "question_code": record["loop_question_code"],
        "question_raw_code": record["loop_raw_code"],
        "text": record["loop_text"],
        "weight": record["loop_weight"],
        "parent_question_id": parent_question_id,
        "parent_question_code": record["parent_question_code"],
        "parent_question_raw_code": record["parent_question_raw_code"],
        "parent_question_text": record["parent_question_text"],
        "parent_question_weight": record["parent_question_weight"],
        "question_types": record["question_types"],
        "data_types": record["data_types"],
        "response_question_text": record["response_question_text"],
        "response_text_matches_loop": record["response_text_matches_loop"],
        "response_subquestions": record["response_subquestions"],
        "response_subquestion_count": record["response_subquestion_count"],
        "response_only_subquestions": record["response_only_subquestions"],
        "structure_only_subquestions": record["structure_only_subquestions"],
        "has_options": record["has_options"],
        "option_row_count": record["option_row_count"],
        "has_maximum_values": record["has_maximum_values"],
        "maximum_value_row_count": record["maximum_value_row_count"],
        "subquestions": record["subquestions"],
        "subquestion_count": record["subquestion_count"],
    }


def make_independent_helper(
    record: dict,
    parent_question_id: str,
) -> str:
    """Construye helper de un bucle independiente."""
    loop_definition = make_loop_definition(
        record=record,
        parent_question_id=parent_question_id,
    )

    payload = {
        "source": SOURCE,
        "source_version": 6,
        "entity": "forms.questions",
        "year": YEAR,
        "source_sheet": record["source_sheet"],
        "source_row_first": record["source_row_first"],
        "source_row_last": record["source_row_last"],
        "source_occurrences": record["source_occurrences"],
        "response_sheet": record["response_sheet"],
        "response_row_first": record["response_row_first"],
        "response_row_last": record["response_row_last"],
        "response_row_count": record["response_row_count"],
        "question_uid": record["question_uid"],
        "natural_key": record["question_uid"],
        "question_code": record["loop_question_code"],
        "question_raw_code": record["loop_raw_code"],
        "parent_question_id": parent_question_id,
        "parent_question_code": record["parent_question_code"],
        "parent_question_raw_code": record["parent_question_raw_code"],
        "component_code": record["component_code"],
        "variable_code": record["variable_code"],
        "indicator_code": record["indicator_code"],
        "parent_question_weight": record["parent_question_weight"],
        "loop_weight": record["loop_weight"],
        "subquestion_count": record["subquestion_count"],
        "subquestion_orders": [
            item["order"]
            for item in record["subquestions"]
        ],
        "question_types": record["question_types"],
        "data_types": record["data_types"],
        "has_options": record["has_options"],
        "option_row_count": record["option_row_count"],
        "has_maximum_values": record["has_maximum_values"],
        "maximum_value_row_count": record["maximum_value_row_count"],
        "is_main_question": False,
        "is_loop": True,
        "is_mixed_question": False,
        "loop_definition": loop_definition,
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def make_mixed_helper(
    current_helper: dict,
    record: dict,
) -> str:
    """Enriquece el helper de la pregunta principal mixta sin reemplazarlo."""
    payload = dict(current_helper)

    payload.update(
        {
            "source": SOURCE,
            "source_version": 6,
            "entity": "forms.questions",
            "year": YEAR,
            "is_main_question": True,
            "is_loop": True,
            "is_mixed_question": True,
            "loop_definition": make_loop_definition(
                record=record,
                parent_question_id=None,
            ),
        }
    )

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def prepare_independent_record(
    record: dict,
    columns: dict,
    form_id: str,
    section_id: str,
    parent: dict,
    existing: dict | None,
) -> dict:
    """Prepara INSERT/UPDATE para un bucle independiente."""
    question_id = (
        existing["question_id"]
        if existing
        else str(uuid7())
    )

    if not uuid7_ok(question_id):
        raise ValueError(f"ID no UUIDv7: {question_id}")

    helper = make_independent_helper(
        record=record,
        parent_question_id=parent["question_id"],
    )

    helper_max = columns["helper"]["max"]

    if helper_max is not None and len(helper) > helper_max:
        raise ValueError(
            f"helper de {record['loop_raw_code']} mide {len(helper)}; "
            f"máximo {helper_max}."
        )

    label = clean(record["loop_raw_code"]) or record["loop_question_code"]
    label_max = columns["label"]["max"]

    if label_max is not None:
        label = label[:label_max]

    description = clean(record["loop_text"]) or label
    description_max = columns["description"]["max"]

    if description_max is not None:
        description = description[:description_max]

    return {
        "id": question_id,
        "form_id": form_id,
        "section_id": section_id,
        "file_id": None,
        "label": label,
        "description": description,
        "helper": helper,
        # La pregunta de bucle se ubica junto a su pregunta principal.
        "display_order": parent["display_order"],
        "required": True,
        "is_loop": True,
    }


async def save_independent_loop(
    conn,
    record: dict,
    update: bool,
) -> None:
    """Inserta o actualiza un bucle independiente."""
    if update:
        sql = """
            UPDATE forms.questions
            SET
                form_id = CAST(:form_id AS uuid),
                section_id = CAST(:section_id AS uuid),
                file_id = CAST(:file_id AS uuid),
                label = :label,
                description = :description,
                helper = :helper,
                display_order = :display_order,
                required = :required,
                is_loop = :is_loop,
                updated_at = NOW()
            WHERE id = CAST(:id AS uuid);
        """
    else:
        sql = """
            INSERT INTO forms.questions (
                id,
                form_id,
                section_id,
                file_id,
                label,
                description,
                helper,
                display_order,
                required,
                is_loop,
                updated_at
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:form_id AS uuid),
                CAST(:section_id AS uuid),
                CAST(:file_id AS uuid),
                :label,
                :description,
                :helper,
                :display_order,
                :required,
                :is_loop,
                NOW()
            );
        """

    await conn.execute(text(sql), record)


async def update_mixed_question(
    conn,
    parent: dict,
    record: dict,
    columns: dict,
) -> None:
    """Actualiza la pregunta principal mixta sin crear una fila adicional."""
    helper = make_mixed_helper(
        current_helper=parent["helper"],
        record=record,
    )

    helper_max = columns["helper"]["max"]

    if helper_max is not None and len(helper) > helper_max:
        raise ValueError(
            f"helper mixto de {record['loop_raw_code']} mide {len(helper)}; "
            f"máximo {helper_max}."
        )

    await conn.execute(
        text(
            """
            UPDATE forms.questions
            SET
                helper = :helper,
                is_loop = TRUE,
                updated_at = NOW()
            WHERE id = CAST(:question_id AS uuid);
            """
        ),
        {
            "question_id": parent["question_id"],
            "helper": helper,
        },
    )


# ---------------------------------------------------------------------
# VALIDACIÓN POSTERIOR
# ---------------------------------------------------------------------


async def validate(
    conn,
    expected_records: list[dict],
) -> None:
    """Valida los 27 bucles, incluida la pregunta mixta."""
    expected_keys = {
        (
            YEAR,
            record["indicator_code"],
            record["loop_question_code"],
        ): record
        for record in expected_records
    }

    result = await conn.execute(
        text(
            """
            SELECT
                question.id::text AS question_id,
                question.helper,
                question.required,
                question.is_loop,
                section_type.label AS section_type,
                form.anno
            FROM forms.questions question
            JOIN forms.forms form
                ON form.id = question.form_id
            JOIN forms.sections section
                ON section.id = question.section_id
            JOIN forms.section_types section_type
                ON section_type.id = section.section_type_id
            WHERE form.anno = :year
              AND question.is_loop = TRUE
            ORDER BY question.id;
            """
        ),
        {"year": YEAR},
    )

    loaded = {}

    for row in result.mappings().all():
        helper = helper_dict(row["helper"])

        if not helper or helper.get("source") not in VALID_SOURCES:
            continue

        if helper.get("entity") != "forms.questions":
            continue

        loop_definition = helper.get("loop_definition")

        if not isinstance(loop_definition, dict):
            continue

        indicator_code = clean(helper.get("indicator_code"))
        loop_question_code = clean(
            loop_definition.get("question_code")
            or helper.get("question_code")
        )

        key = (
            YEAR,
            indicator_code,
            loop_question_code,
        )

        if key not in expected_keys:
            continue

        if key in loaded:
            raise ValueError(
                f"El bucle {key} aparece más de una vez en PostgreSQL."
            )

        loaded[key] = {
            "row": row,
            "helper": helper,
            "loop_definition": loop_definition,
        }

    missing = set(expected_keys) - set(loaded)

    if missing:
        raise ValueError(
            "No se cargaron todos los bucles esperados. "
            f"Faltan: {sorted(missing)[:20]}"
        )

    mixed_count = 0

    for key, expected in expected_keys.items():
        loaded_item = loaded[key]
        row = loaded_item["row"]
        helper = loaded_item["helper"]
        loop_definition = loaded_item["loop_definition"]

        if not uuid7_ok(row["question_id"]):
            raise ValueError(
                f"Bucle sin UUIDv7: {row['question_id']}"
            )

        if (clean(row["section_type"]) or "").upper() != "INDICADOR":
            raise ValueError(
                f"Bucle no conectado a INDICADOR: {row['question_id']}"
            )

        if row["required"] is not True or row["is_loop"] is not True:
            raise ValueError(
                f"required/is_loop incorrectos: {row['question_id']}"
            )

        subquestions = loop_definition.get("subquestions")

        if not isinstance(subquestions, list) or not subquestions:
            raise ValueError(
                f"El bucle {key} no conserva sus subpreguntas."
            )

        if len(subquestions) != int(expected["subquestion_count"]):
            raise ValueError(
                f"El bucle {key} tiene {len(subquestions)} subpreguntas; "
                f"se esperaban {expected['subquestion_count']}."
            )

        is_main = helper.get("is_main_question") is True
        is_mixed = helper.get("is_mixed_question") is True

        if expected["is_mixed_question"]:
            mixed_count += 1

            if not is_main or not is_mixed:
                raise ValueError(
                    f"El bucle mixto {key} no conserva sus indicadores."
                )

            if loop_definition.get("parent_question_id") is not None:
                raise ValueError(
                    f"El bucle mixto {key} no debe tener parent_question_id."
                )
        else:
            if is_main or is_mixed:
                raise ValueError(
                    f"El bucle independiente {key} quedó marcado como principal."
                )

            if not uuid7_ok(loop_definition.get("parent_question_id")):
                raise ValueError(
                    f"El bucle independiente {key} no tiene padre UUIDv7."
                )

    if mixed_count != EXPECTED_MIXED_LOOP_COUNT:
        raise ValueError(
            f"Se esperaban {EXPECTED_MIXED_LOOP_COUNT} bucles mixtos y se "
            f"validaron {mixed_count}."
        )

    logger.info(
        "forms.questions loop validation passed successfully. "
        f"Validated loops: {len(expected_keys)}."
    )


# ---------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------------------------------------------------


async def upgrade(gh, api) -> None:
    """Puebla los bucles de 2023."""
    del gh
    del api

    path = Path(FILE_PATH)

    logger.info(
        f"Starting loop questions population from {path}"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {path}"
        )

    try:
        excel = pd.ExcelFile(path)
        records = load_loop_records(excel)
        add_response_metadata(excel, records)

        logger.info(
            f"Unique loop definitions found: {len(records)}"
        )

        async with async_engine.begin() as conn:
            columns = await table_columns(conn)
            form_id = await form_id_2023(conn)
            indicators_by_code, indicators_by_labels = (
                await indicator_maps(conn)
            )
            parents = await main_question_map(conn)
            existing_independent = await existing_independent_loop_map(conn)

            inserted = 0
            updated = 0
            mixed_updated = 0

            for record in records:
                section_id = indicators_by_code.get(
                    (YEAR, record["indicator_code"])
                )

                if section_id is None:
                    section_id = indicators_by_labels.get(
                        record["indicator_fallback_key"]
                    )

                if section_id is None:
                    raise ValueError(
                        f"No se encontró indicador para "
                        f"{record['loop_raw_code']} "
                        f"({record['indicator_code']})."
                    )

                parent_key = (
                    YEAR,
                    record["indicator_code"],
                    record["parent_question_code"],
                )
                parent = parents.get(parent_key)

                if parent is None:
                    raise ValueError(
                        "No se encontró la pregunta principal "
                        f"{record['parent_question_raw_code']} para "
                        f"{record['loop_raw_code']}. Ejecuta antes "
                        "11d_seed_questions.py."
                    )

                if parent["section_id"] != section_id:
                    raise ValueError(
                        f"La pregunta principal {record['parent_question_raw_code']} "
                        "y su bucle quedaron asociados a indicadores diferentes."
                    )

                if record["is_mixed_question"]:
                    if (
                        record["loop_question_code"]
                        != record["parent_question_code"]
                    ):
                        raise ValueError(
                            "Una pregunta mixta debe usar el mismo código para "
                            "pregunta principal y bucle."
                        )

                    await update_mixed_question(
                        conn=conn,
                        parent=parent,
                        record=record,
                        columns=columns,
                    )
                    mixed_updated += 1
                    continue

                loop_key = (
                    YEAR,
                    record["indicator_code"],
                    record["loop_question_code"],
                )
                existing = existing_independent.get(loop_key)

                prepared = prepare_independent_record(
                    record=record,
                    columns=columns,
                    form_id=form_id,
                    section_id=section_id,
                    parent=parent,
                    existing=existing,
                )

                await save_independent_loop(
                    conn=conn,
                    record=prepared,
                    update=existing is not None,
                )

                if existing:
                    updated += 1
                else:
                    inserted += 1

            await validate(
                conn=conn,
                expected_records=records,
            )

        logger.info(
            "Loop questions population completed successfully. "
            f"Inserted independent loops: {inserted}. "
            f"Updated independent loops: {updated}. "
            f"Updated mixed main questions: {mixed_updated}."
        )

    except Exception as exc:
        logger.exception(
            f"Failed to populate loop questions: {exc}"
        )
        raise
