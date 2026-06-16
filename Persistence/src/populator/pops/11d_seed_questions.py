"""Puebla las preguntas principales del IIP en forms.questions.

Fuente: Estructura_IIP.xlsx
Años activos: 2019, 2021 y 2023.

Regla especial de 2023:
- Pregunta 28.1 aparece como pregunta principal y también como bucle.
- Se conserva UNA sola fila en forms.questions.
- Esa fila queda con is_main_question=True e is_loop=True.
- Su respuesta directa y su definición repetible se modelarán posteriormente
  mediante field_groups/card_templates, sin duplicar la pregunta.
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


logger = get_logger("pop/questions")

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)
DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023)
SOURCE = "Estructura_IIP.xlsx"
VALID_SOURCES = {"Estructura IIP.xlsx", "Estructura_IIP.xlsx"}


def active_years() -> tuple[int, ...]:
    raw = os.getenv("IIP_ACTIVE_YEARS")
    if not raw:
        return DEFAULT_ACTIVE_YEARS

    years = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            years.append(int(item))
        except ValueError as exc:
            raise ValueError(
                f"Año inválido en IIP_ACTIVE_YEARS: {item!r}"
            ) from exc

    if not years or len(years) != len(set(years)):
        raise ValueError(
            f"IIP_ACTIVE_YEARS debe contener años únicos y válidos: {years}"
        )
    return tuple(years)


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


def norm(value):
    value = clean(value)
    if value is None:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", value.lower()).strip()


def number(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, bool):
        raise ValueError(f"No se puede interpretar como número: {value!r}")

    if isinstance(value, (int, float)):
        result = float(value)
        return None if math.isnan(result) else result

    value = clean(value)
    if value is None:
        return None

    try:
        return float(
            value.replace("\u00a0", "").replace(" ", "").replace(",", ".")
        )
    except ValueError as exc:
        raise ValueError(f"Valor numérico inválido: {value!r}") from exc


def same_number(left, right):
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-9)


def suffix(value):
    value = clean(value)
    if value is None:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)*)", value)
    if not match:
        return None
    return match.group(1).replace(".", "_").replace(",", "_")


def code(prefix, value):
    result = suffix(value)
    if result:
        return f"{prefix}{result}"
    normalized = re.sub(
        r"[^a-z0-9]+", "_", norm(value) or "sin_codigo"
    ).strip("_")
    return f"{prefix}{normalized}"


def uuid7_ok(value):
    try:
        return UUID(str(value)).version == 7
    except Exception:
        return False


def helper_dict(value):
    try:
        value = json.loads(value) if value else None
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def unique(values):
    output, seen = [], set()
    for value in values:
        value = clean(value)
        if value is None:
            continue
        key = norm(value)
        if key not in seen:
            seen.add(key)
            output.append(value)
    return output


def read_sheet(excel, name):
    if name not in excel.sheet_names:
        raise ValueError(
            f"No existe la hoja {name!r}. Hojas disponibles: {excel.sheet_names}"
        )
    df = pd.read_excel(excel, sheet_name=name, dtype=object)
    df.columns = [str(column).strip() for column in df.columns]
    return df


def normalize_questions(df, year):
    columns = {
        "c_raw": "Componente",
        "c_label": f"Componente {year}",
        "v_raw": "Variable",
        "v_label": f"Variable {year}",
        "i_raw": "Indicador",
        "i_label": f"Indicador {year}",
        "q_raw": "Pregunta",
        "q_text": f"Pregunta {year}",
        "q_weight": "Maxp",
        "loop_raw": "Bucle",
        "loop_text": f"Bucle {year}",
        "loop_weight": "Maxb",
        "sub_order": "Orden_subpregunta_bucle",
        "sub_text": "Subpregunta_bucle",
        "sub_weight": "Max_subpregunta_bucle",
    }

    missing = set(columns.values()) - set(df.columns)
    if missing:
        raise ValueError(
            f"Faltan columnas en la hoja {year}: {sorted(missing)}"
        )

    data = pd.DataFrame(
        {
            "year": year,
            "row": df.index + 2,
            **{name: df[column] for name, column in columns.items()},
        }
    )

    for column in data.columns:
        if column not in {"year", "row"}:
            data[column] = data[column].apply(clean)

    hierarchy = ["c_raw", "c_label", "v_raw", "v_label", "i_raw", "i_label"]
    data[hierarchy] = data[hierarchy].ffill()

    data = data[
        data["c_raw"].notna()
        & data["c_label"].notna()
        & data["v_raw"].notna()
        & data["v_label"].notna()
        & data["i_raw"].notna()
        & data["i_label"].notna()
        & data["q_raw"].notna()
        & data["q_text"].notna()
    ].copy()

    if data.empty:
        raise ValueError(f"La hoja {year} no produjo preguntas válidas.")

    data["q_weight"] = data["q_weight"].apply(number)
    data["loop_weight"] = data["loop_weight"].apply(number)
    data["sub_weight"] = data["sub_weight"].apply(number)

    data["c_code"] = data["c_raw"].apply(lambda value: code("C", value))
    data["v_code"] = data.apply(
        lambda row: f"{row['c_code']}_{code('V', row['v_raw'])}", axis=1
    )
    data["i_code"] = data.apply(
        lambda row: f"{row['v_code']}_{code('I', row['i_raw'])}", axis=1
    )
    data["q_code"] = data["q_raw"].apply(lambda value: code("P", value))
    data["loop_code"] = data["loop_raw"].apply(
        lambda value: code("P", value) if clean(value) else None
    )

    return data


def validate_base(existing, candidate, key):
    conflicts = []
    for field in (
        "c_code",
        "v_code",
        "i_code",
        "q_code",
        "q_raw",
        "q_text",
    ):
        left = existing[field]
        right = candidate[field]
        equal = norm(left) == norm(right) if field in {"q_raw", "q_text"} else left == right
        if not equal:
            conflicts.append(f"{field}: {left!r} != {right!r}")

    if not same_number(existing["q_weight"], candidate["q_weight"]):
        conflicts.append(
            f"q_weight: {existing['q_weight']!r} != {candidate['q_weight']!r}"
        )

    if conflicts:
        raise ValueError(
            f"Información contradictoria para {key}. "
            f"Fila inicial {existing['source_row_first']}; "
            f"fila conflictiva {candidate['source_row_first']}. "
            + "; ".join(conflicts)
        )


def add_self_loop(record, row):
    loop_raw = clean(row["loop_raw"])
    loop_code = clean(row["loop_code"])
    if loop_raw is None or loop_code != record["q_code"]:
        return

    loop_text = clean(row["loop_text"])
    if loop_text is None:
        raise ValueError(
            f"Bucle mixto sin texto en fila {int(row['row'])}: {record['q_raw']}"
        )

    definition = record.get("loop_definition")
    if definition is None:
        definition = {
            "question_code": loop_code,
            "question_raw_code": loop_raw,
            "text": loop_text,
            "weight": row["loop_weight"],
            "source_row_first": int(row["row"]),
            "source_row_last": int(row["row"]),
            "source_occurrences": 0,
            "subquestions": OrderedDict(),
        }
        record["loop_definition"] = definition
    else:
        if norm(definition["text"]) != norm(loop_text):
            raise ValueError(
                f"Texto de bucle contradictorio para {record['q_raw']} "
                f"en fila {int(row['row'])}."
            )
        if not same_number(definition["weight"], row["loop_weight"]):
            raise ValueError(
                f"Maxb contradictorio para {record['q_raw']} "
                f"en fila {int(row['row'])}."
            )
        definition["source_row_last"] = int(row["row"])

    definition["source_occurrences"] += 1

    sub_text = clean(row["sub_text"])
    if sub_text is None:
        return

    sub_order_value = number(row["sub_order"])
    if (
        sub_order_value is None
        or not sub_order_value.is_integer()
        or sub_order_value <= 0
    ):
        raise ValueError(
            f"Orden de subpregunta inválido en fila {int(row['row'])}: "
            f"{row['sub_order']!r}"
        )

    sub_order = int(sub_order_value)
    candidate = {
        "order": sub_order,
        "text": sub_text,
        "weight": row["sub_weight"],
    }
    previous = definition["subquestions"].get(sub_order)
    if previous is not None and (
        norm(previous["text"]) != norm(candidate["text"])
        or not same_number(previous["weight"], candidate["weight"])
    ):
        raise ValueError(
            f"Subpregunta contradictoria en {record['q_raw']}, orden {sub_order}."
        )
    definition["subquestions"][sub_order] = candidate


def build_question_records(data):
    registry = OrderedDict()

    for _, row in data.iterrows():
        year = int(row["year"])
        key = (year, row["i_code"], row["q_code"])
        candidate = {
            "year": year,
            "source_sheet": str(year),
            "source_row_first": int(row["row"]),
            "source_row_last": int(row["row"]),
            "source_occurrences": 1,
            "c_code": row["c_code"],
            "v_code": row["v_code"],
            "i_code": row["i_code"],
            "c_label": row["c_label"],
            "v_label": row["v_label"],
            "i_label": row["i_label"],
            "q_code": row["q_code"],
            "q_raw": row["q_raw"],
            "q_text": row["q_text"],
            "q_weight": row["q_weight"],
            "child_loop_codes": [],
            "loop_definition": None,
            "indicator_fallback_key": (
                year,
                norm(row["c_label"]),
                norm(row["v_label"]),
                norm(row["i_label"]),
            ),
        }

        current = registry.get(key)
        if current is None:
            registry[key] = candidate
            current = candidate
        else:
            validate_base(current, candidate, key)
            current["source_row_last"] = int(row["row"])
            current["source_occurrences"] += 1

        loop_code = clean(row["loop_code"])
        if loop_code:
            if loop_code == current["q_code"]:
                add_self_loop(current, row)
            elif loop_code not in current["child_loop_codes"]:
                current["child_loop_codes"].append(loop_code)

    records = list(registry.values())
    records.sort(key=lambda item: (item["source_row_first"], item["q_code"]))

    for display_order, record in enumerate(records, start=1):
        definition = record.get("loop_definition")
        if definition is not None:
            definition["subquestions"] = [
                definition["subquestions"][order]
                for order in sorted(definition["subquestions"])
            ]
            orders = [item["order"] for item in definition["subquestions"]]
            if orders != list(range(1, len(orders) + 1)):
                raise ValueError(
                    f"Órdenes no consecutivos en el bucle mixto {record['q_raw']}: "
                    f"{orders}"
                )
            definition["subquestion_count"] = len(orders)

        record["display_order"] = display_order
        record["is_mixed_question"] = definition is not None
        record["is_loop"] = definition is not None
        record["question_uid"] = (
            f"{record['year']}|{record['i_code']}|{record['q_code']}"
        )

    return records


def response_summaries(df, year):
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
        raise ValueError(
            f"Faltan columnas en Respuestas_{year}: {sorted(missing)}"
        )

    has_subquestion = "Texto_subpregunta" in df.columns
    grouped = OrderedDict()

    for index, row in df.iterrows():
        raw = clean(row["Pregunta"])
        question_text = clean(row["Texto_pregunta"])
        if raw is None or question_text is None:
            continue
        grouped.setdefault(raw, []).append(
            {
                "row": int(index) + 2,
                "text": question_text,
                "subquestion": clean(row["Texto_subpregunta"])
                if has_subquestion
                else None,
                "type": clean(row["Tipo_pregunta"]),
                "data_type": clean(row["Tipo_dato"]),
                "option": clean(row["Texto_opcion"]),
                "maximum": clean(row["Valor_maximo"]),
            }
        )

    output = {}
    for raw, rows in grouped.items():
        texts = unique(row["text"] for row in rows)
        if len({norm(value) for value in texts}) != 1:
            raise ValueError(
                f"Respuestas_{year} contiene textos diferentes para {raw}: {texts}"
            )
        subquestions = unique(row["subquestion"] for row in rows)
        output[raw] = {
            "response_sheet": f"Respuestas_{year}",
            "response_row_first": min(row["row"] for row in rows),
            "response_row_last": max(row["row"] for row in rows),
            "response_row_count": len(rows),
            "response_question_text": texts[0],
            "question_types": unique(row["type"] for row in rows),
            "data_types": unique(row["data_type"] for row in rows),
            "response_subquestion_count": len(subquestions),
            "direct_response_row_count": sum(
                row["subquestion"] is None for row in rows
            ),
            "has_options": any(row["option"] is not None for row in rows),
            "option_row_count": sum(row["option"] is not None for row in rows),
            "has_maximum_values": any(
                row["maximum"] is not None for row in rows
            ),
            "maximum_value_row_count": sum(
                row["maximum"] is not None for row in rows
            ),
        }
    return output


def attach_responses(records, summaries, year):
    used = set()
    for record in records:
        summary = summaries.get(record["q_raw"])
        if summary is None:
            raise ValueError(
                f"{record['q_raw']} de la hoja {year} no aparece en "
                f"Respuestas_{year}."
            )
        if norm(record["q_text"]) != norm(summary["response_question_text"]):
            raise ValueError(
                f"El texto de {record['q_raw']} no coincide entre {year} y "
                f"Respuestas_{year}."
            )
        record.update(summary)
        used.add(record["q_raw"])
    return used


def make_helper(record):
    payload = {
        "source": SOURCE,
        "source_version": 5,
        "entity": "forms.questions",
        "year": record["year"],
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
        "question_code": record["q_code"],
        "question_raw_code": record["q_raw"],
        "component_code": record["c_code"],
        "variable_code": record["v_code"],
        "indicator_code": record["i_code"],
        "question_weight": record["q_weight"],
        "question_types": record["question_types"],
        "data_types": record["data_types"],
        "response_subquestion_count": record["response_subquestion_count"],
        "direct_response_row_count": record["direct_response_row_count"],
        "has_options": record["has_options"],
        "option_row_count": record["option_row_count"],
        "has_maximum_values": record["has_maximum_values"],
        "maximum_value_row_count": record["maximum_value_row_count"],
        "child_loop_codes": record["child_loop_codes"],
        "is_main_question": True,
        "is_loop": record["is_loop"],
        "is_mixed_question": record["is_mixed_question"],
    }
    if record["loop_definition"] is not None:
        payload["loop_definition"] = record["loop_definition"]
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


async def table_columns(conn):
    result = await conn.execute(
        text(
            """
            SELECT column_name, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_schema='forms' AND table_name='questions';
            """
        )
    )
    rows = result.mappings().all()
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
        raise ValueError(f"Faltan columnas en forms.questions: {sorted(missing)}")
    return columns


async def form_map(conn, years):
    result = await conn.execute(
        text("SELECT anno, id::text AS id FROM forms.forms ORDER BY anno")
    )
    grouped = {}
    for row in result.mappings().all():
        year = int(row["anno"])
        if year in years:
            grouped.setdefault(year, []).append(row["id"])

    output = {}
    for year in years:
        ids = grouped.get(year, [])
        if len(ids) != 1:
            raise ValueError(
                f"Debe existir un único formulario {year}; encontrados: {len(ids)}."
            )
        if not uuid7_ok(ids[0]):
            raise ValueError(f"form_id {year} no es UUIDv7: {ids[0]}")
        output[year] = ids[0]
    return output


async def indicator_maps(conn, years):
    result = await conn.execute(
        text(
            """
            SELECT f.anno, c.label AS c_label, v.label AS v_label,
                   i.label AS i_label, i.id::text AS i_id, i.helper
            FROM forms.sections i
            JOIN forms.section_types ti ON ti.id=i.section_type_id
              AND UPPER(TRIM(ti.label))='INDICADOR'
            JOIN forms.sections v ON v.id=i.parent_id
            JOIN forms.sections c ON c.id=v.parent_id
            JOIN forms.forms f ON f.id=i.form_id
            ORDER BY f.anno, i.id;
            """
        )
    )

    by_code, by_labels = {}, {}
    for row in result.mappings().all():
        year = int(row["anno"])
        if year not in years:
            continue
        if not uuid7_ok(row["i_id"]):
            raise ValueError(f"Indicador no UUIDv7: {row['i_id']}")

        helper = helper_dict(row["helper"])
        if (
            helper
            and helper.get("source") in VALID_SOURCES
            and helper.get("entity") == "forms.sections"
            and helper.get("level") == "INDICADOR"
        ):
            indicator_code = clean(helper.get("code"))
            if indicator_code:
                key = (year, indicator_code)
                if key in by_code and by_code[key] != row["i_id"]:
                    raise ValueError(f"Indicador duplicado: {key}")
                by_code[key] = row["i_id"]

        label_key = (
            year,
            norm(row["c_label"]),
            norm(row["v_label"]),
            norm(row["i_label"]),
        )
        if label_key in by_labels and by_labels[label_key] != row["i_id"]:
            raise ValueError(f"Indicador ambiguo por etiquetas: {label_key}")
        by_labels[label_key] = row["i_id"]

    return by_code, by_labels


async def existing_main_questions(conn, years):
    result = await conn.execute(
        text(
            """
            SELECT q.id::text AS q_id, q.label, q.helper, q.is_loop,
                   f.anno, s.helper AS section_helper
            FROM forms.questions q
            JOIN forms.forms f ON f.id=q.form_id
            LEFT JOIN forms.sections s ON s.id=q.section_id
            ORDER BY f.anno, q.id;
            """
        )
    )

    output = {}
    for row in result.mappings().all():
        year = int(row["anno"])
        if year not in years:
            continue

        helper = helper_dict(row["helper"])
        if not helper or helper.get("source") not in VALID_SOURCES:
            continue
        if helper.get("entity") != "forms.questions":
            continue
        if helper.get("is_main_question") is not True:
            continue

        section_helper = helper_dict(row["section_helper"]) or {}
        q_code = clean(helper.get("question_code")) or code("P", row["label"])
        i_code = clean(helper.get("indicator_code")) or clean(
            section_helper.get("code")
        )
        if i_code is None:
            raise ValueError(
                f"No se pudo identificar indicator_code de la pregunta {row['q_id']}."
            )

        key = (year, i_code, q_code)
        if key in output:
            raise ValueError(
                f"Preguntas principales duplicadas para {key}: "
                f"{output[key]} y {row['q_id']}"
            )
        if not uuid7_ok(row["q_id"]):
            raise ValueError(f"Pregunta no UUIDv7: {row['q_id']}")
        output[key] = row["q_id"]

    return output


def db_record(record, columns, form_id, section_id, existing_id):
    helper = make_helper(record)
    helper_max = columns["helper"]["max"]
    if helper_max is not None and len(helper) > helper_max:
        raise ValueError(
            f"helper de {record['q_raw']} mide {len(helper)}; máximo {helper_max}."
        )

    q_id = existing_id or str(uuid7())
    if not uuid7_ok(q_id):
        raise ValueError(f"ID no UUIDv7: {q_id}")

    label = clean(record["q_raw"]) or record["q_code"]
    label_max = columns["label"]["max"]
    if label_max is not None:
        label = label[:label_max]

    description = clean(record["q_text"]) or "Sin texto de pregunta registrado."
    description_max = columns["description"]["max"]
    if description_max is not None:
        description = description[:description_max]

    return {
        "id": q_id,
        "form_id": form_id,
        "section_id": section_id,
        "file_id": None,
        "label": label,
        "description": description,
        "helper": helper,
        "display_order": int(record["display_order"]),
        "required": True,
        "is_loop": bool(record["is_loop"]),
    }


async def save_question(conn, record, update):
    if update:
        sql = """
            UPDATE forms.questions SET
              form_id=CAST(:form_id AS uuid),
              section_id=CAST(:section_id AS uuid),
              file_id=CAST(:file_id AS uuid),
              label=:label,
              description=:description,
              helper=:helper,
              display_order=:display_order,
              required=:required,
              is_loop=:is_loop,
              updated_at=NOW()
            WHERE id=CAST(:id AS uuid);
        """
    else:
        sql = """
            INSERT INTO forms.questions (
              id, form_id, section_id, file_id, label, description, helper,
              display_order, required, is_loop, updated_at
            ) VALUES (
              CAST(:id AS uuid), CAST(:form_id AS uuid),
              CAST(:section_id AS uuid), CAST(:file_id AS uuid),
              :label, :description, :helper, :display_order,
              :required, :is_loop, NOW()
            );
        """
    await conn.execute(text(sql), record)


async def validate(conn, years, expected):
    expected_by_key = {
        (item["year"], item["i_code"], item["q_code"]): item
        for item in expected
    }

    result = await conn.execute(
        text(
            """
            SELECT q.id::text AS q_id, q.form_id::text AS q_form_id,
                   q.section_id::text AS section_id, q.helper,
                   q.required, q.is_loop, f.anno,
                   s.form_id::text AS section_form_id,
                   s.helper AS section_helper, st.label AS section_type
            FROM forms.questions q
            JOIN forms.forms f ON f.id=q.form_id
            LEFT JOIN forms.sections s ON s.id=q.section_id
            LEFT JOIN forms.section_types st ON st.id=s.section_type_id
            ORDER BY f.anno, q.id;
            """
        )
    )

    loaded = {}
    for row in result.mappings().all():
        year = int(row["anno"])
        if year not in years:
            continue
        helper = helper_dict(row["helper"])
        if (
            not helper
            or helper.get("source") not in VALID_SOURCES
            or helper.get("entity") != "forms.questions"
            or helper.get("is_main_question") is not True
        ):
            continue
        key = (
            year,
            clean(helper.get("indicator_code")),
            clean(helper.get("question_code")),
        )
        if key in expected_by_key:
            if key in loaded:
                raise ValueError(f"Pregunta principal duplicada en SQL: {key}")
            loaded[key] = row

    missing = set(expected_by_key) - set(loaded)
    if missing:
        raise ValueError(f"Faltan preguntas principales: {sorted(missing)[:20]}")

    for key, item in expected_by_key.items():
        row = loaded[key]
        if not uuid7_ok(row["q_id"]):
            raise ValueError(f"Pregunta sin UUIDv7: {key}")
        if row["section_id"] is None or row["section_form_id"] is None:
            raise ValueError(f"Pregunta sin indicador válido: {key}")
        if row["q_form_id"] != row["section_form_id"]:
            raise ValueError(f"Pregunta e indicador de formularios distintos: {key}")
        if (clean(row["section_type"]) or "").upper() != "INDICADOR":
            raise ValueError(f"Pregunta no conectada a INDICADOR: {key}")
        if row["required"] is not True:
            raise ValueError(f"required incorrecto: {key}")
        if row["is_loop"] is not bool(item["is_loop"]):
            raise ValueError(
                f"is_loop incorrecto para {key}: "
                f"SQL={row['is_loop']} esperado={item['is_loop']}"
            )

    logger.info(
        f"forms.questions validation passed. Main questions: {len(expected_by_key)}"
    )


async def upgrade(gh, api):
    del gh, api

    path = Path(FILE_PATH)
    years = active_years()
    logger.info(f"Starting main questions population from {path}; years={years}")

    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    try:
        excel = pd.ExcelFile(path)
        all_records = []

        for year in years:
            structure = read_sheet(excel, str(year))
            responses = read_sheet(excel, f"Respuestas_{year}")

            records = build_question_records(normalize_questions(structure, year))
            summaries = response_summaries(responses, year)
            used = attach_responses(records, summaries, year)

            extra = set(summaries) - used
            if extra:
                logger.info(
                    f"Year {year}: {len(extra)} códigos de respuestas no son "
                    f"preguntas principales. Muestra: {sorted(extra)[:15]}"
                )

            mixed = [item["q_raw"] for item in records if item["is_mixed_question"]]
            logger.info(
                f"Year {year}: {len(records)} preguntas principales; "
                f"mixtas pregunta+bucle: {mixed or 'ninguna'}."
            )
            all_records.extend(records)

        async with async_engine.begin() as conn:
            columns = await table_columns(conn)
            forms = await form_map(conn, years)
            indicators_by_code, indicators_by_labels = await indicator_maps(conn, years)
            existing = await existing_main_questions(conn, years)

            source_keys = {
                (item["year"], item["i_code"], item["q_code"])
                for item in all_records
            }
            stale = set(existing) - source_keys
            if stale:
                logger.warning(
                    f"Preguntas principales antiguas no presentes en el Excel: "
                    f"{len(stale)}. Muestra: {sorted(stale)[:15]}"
                )

            inserted = updated = 0
            unresolved = []

            for item in all_records:
                section_id = indicators_by_code.get((item["year"], item["i_code"]))
                if section_id is None:
                    section_id = indicators_by_labels.get(
                        item["indicator_fallback_key"]
                    )
                if section_id is None:
                    unresolved.append(item)
                    continue

                key = (item["year"], item["i_code"], item["q_code"])
                existing_id = existing.get(key)
                prepared = db_record(
                    item, columns, forms[item["year"]], section_id, existing_id
                )
                await save_question(conn, prepared, update=existing_id is not None)
                if existing_id:
                    updated += 1
                else:
                    inserted += 1

            if unresolved:
                raise ValueError(
                    "No se pudo resolver el indicador de algunas preguntas. "
                    f"Muestra: {[(x['year'], x['q_raw'], x['i_code']) for x in unresolved[:20]]}"
                )

            await validate(conn, years, all_records)

        logger.info(
            f"Main questions completed. Inserted: {inserted}. Updated: {updated}."
        )

    except Exception as exc:
        logger.exception(f"Failed to populate main questions: {exc}")
        raise
