"""Poblado de forms.sections desde Estructura_IIP.xlsx.

Carga la jerarquía metodológica del Índice de Innovación Pública:

    COMPONENTE
        └── VARIABLE
              └── INDICADOR

Relaciones creadas:

    forms.sections.form_id
        -> forms.forms.id

    forms.sections.section_type_id
        -> forms.section_types.id

    forms.sections.parent_id
        -> forms.sections.id de la sección padre

Alcance actual:
    - 2019
    - 2021
    - 2023

Reglas:
- Cada año corresponde a un formulario independiente.
- Los registros nuevos usan UUID versión 7.
- Los registros existentes conservan su UUIDv7.
- El script actualiza registros existentes y evita duplicados.
- COMPONENTE tiene parent_id = NULL.
- VARIABLE apunta al COMPONENTE.
- INDICADOR apunta a la VARIABLE.
- file_id se deja en NULL.
- Maxc, Maxv y Maxi se conservan en helper.
- El script reconoce registros creados con el nombre anterior
  "Estructura IIP.xlsx" y con el nombre nuevo "Estructura_IIP.xlsx".
- Las filas repetidas por preguntas o bucles no generan secciones duplicadas.
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


logger = get_logger("pop/sections")


# ---------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------

LOCAL_IIP_STRUCTURE_FILE = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023)

SECTION_LEVELS = (
    "COMPONENTE",
    "VARIABLE",
    "INDICADOR",
)

LEVEL_ORDER = {
    "COMPONENTE": 1,
    "VARIABLE": 2,
    "INDICADOR": 3,
}

PARENT_LEVEL = {
    "COMPONENTE": None,
    "VARIABLE": "COMPONENTE",
    "INDICADOR": "VARIABLE",
}

WEIGHT_SOURCE_COLUMN = {
    "COMPONENTE": "Maxc",
    "VARIABLE": "Maxv",
    "INDICADOR": "Maxi",
}

# Permite reconocer los registros creados con la versión anterior.
MANAGED_SOURCE_NAMES = {
    "Estructura IIP.xlsx",
    "Estructura_IIP.xlsx",
}

CURRENT_SOURCE_NAME = "Estructura_IIP.xlsx"


# ---------------------------------------------------------------------
# FUNCIONES GENERALES
# ---------------------------------------------------------------------

def get_active_years() -> tuple[int, ...]:
    """Obtiene los años activos desde la variable de entorno.

    Ejemplo opcional:

        IIP_ACTIVE_YEARS=2019,2021,2023
    """
    raw_value = os.getenv("IIP_ACTIVE_YEARS")

    if not raw_value:
        return DEFAULT_ACTIVE_YEARS

    years = []

    for value in raw_value.split(","):
        value = value.strip()

        if not value:
            continue

        try:
            years.append(int(value))
        except ValueError as exc:
            raise ValueError(
                "IIP_ACTIVE_YEARS debe contener años separados por coma. "
                f"Valor inválido: {value!r}"
            ) from exc

    if not years:
        raise ValueError("IIP_ACTIVE_YEARS no contiene años válidos.")

    if len(years) != len(set(years)):
        raise ValueError(
            f"IIP_ACTIVE_YEARS contiene años duplicados: {years}"
        )

    return tuple(years)


def clean_text(value):
    """Convierte valores vacíos, NaN y espacios en None."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    value = str(value).strip()

    if value == "":
        return None

    return value


def normalize_key(value):
    """Normaliza texto para comparaciones robustas."""
    value = clean_text(value)

    if value is None:
        return None

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )
    value = value.lower()
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def parse_number(value):
    """Convierte Maxc, Maxv o Maxi a número.

    Los vacíos permanecen como None.

    Ejemplos:
        25       -> 25.0
        "7,7"    -> 7.7
        "5.15625" -> 5.15625
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, bool):
        raise ValueError(
            f"No se puede interpretar un booleano como ponderación: {value}"
        )

    if isinstance(value, (int, float)):
        numeric_value = float(value)

        if math.isnan(numeric_value):
            return None

        return numeric_value

    text_value = clean_text(value)

    if text_value is None:
        return None

    text_value = (
        text_value
        .replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        return float(text_value)
    except ValueError as exc:
        raise ValueError(
            f"No se pudo convertir la ponderación {value!r} a número."
        ) from exc


def numbers_equal(left, right, tolerance: float = 1e-9) -> bool:
    """Compara ponderaciones considerando tolerancia decimal."""
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


def extract_code_suffix(value):
    """Extrae el segmento numérico completo de un código.

    Ejemplos:
        Componente 1 -> 1
        Variable 4   -> 4
        Indicador 3.1 -> 3_1
    """
    value = clean_text(value)

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


def make_code(prefix: str, raw_code) -> str:
    """Construye un código técnico estable."""
    suffix = extract_code_suffix(raw_code)

    if suffix:
        return f"{prefix}{suffix}"

    normalized = normalize_key(raw_code) or "sin_codigo"
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = normalized.strip("_")

    return f"{prefix}{normalized}"


def make_display_order(raw_code) -> int:
    """Genera un orden entero a partir del código de la sección."""
    suffix = extract_code_suffix(raw_code)

    if suffix is None:
        return 0

    parts = [
        int(part)
        for part in suffix.split("_")
        if part.isdigit()
    ]

    if not parts:
        return 0

    order = parts[0] * 1000

    if len(parts) >= 2:
        order += parts[1]

    if len(parts) >= 3:
        order = order * 1000 + parts[2]

    return order


def is_uuidv7(value) -> bool:
    """Valida UUID versión 7."""
    value = clean_text(value)

    if value is None:
        return False

    try:
        return UUID(value).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    """Genera un UUID versión 7."""
    return str(uuid7())


def truncate_text(value, max_length):
    """Recorta texto únicamente cuando la columna tiene límite."""
    value = clean_text(value)

    if value is None:
        return None

    if max_length is None:
        return value

    if len(value) <= max_length:
        return value

    return value[:max_length]


def parse_helper(helper_text):
    """Convierte helper JSON en diccionario."""
    helper_text = clean_text(helper_text)

    if helper_text is None:
        return None

    try:
        parsed = json.loads(helper_text)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(parsed, dict):
        return None

    return parsed


def is_managed_helper(helper: dict | None) -> bool:
    """Determina si el registro fue generado por este proceso."""
    if not helper:
        return False

    if helper.get("entity") != "forms.sections":
        return False

    return helper.get("source") in MANAGED_SOURCE_NAMES


# ---------------------------------------------------------------------
# LECTURA Y NORMALIZACIÓN DEL EXCEL
# ---------------------------------------------------------------------

def required_columns_for_year(year: int) -> dict[str, str]:
    """Define las columnas exactas esperadas en la hoja anual."""
    return {
        "component_code": "Componente",
        "component_label": f"Componente {year}",
        "component_weight": "Maxc",
        "variable_code": "Variable",
        "variable_label": f"Variable {year}",
        "variable_weight": "Maxv",
        "indicator_code": "Indicador",
        "indicator_label": f"Indicador {year}",
        "indicator_weight": "Maxi",
    }


def read_structure_sheet(
    excel_file: pd.ExcelFile,
    year: int,
) -> pd.DataFrame:
    """Lee y valida una hoja anual.

    Para los años activos, la hoja es obligatoria. No se omite de forma
    silenciosa porque eso produciría formularios incompletos.
    """
    sheet_name = str(year)

    if sheet_name not in excel_file.sheet_names:
        raise ValueError(
            f"No existe la hoja obligatoria '{sheet_name}' en "
            f"{Path(excel_file.io).name}. "
            f"Hojas disponibles: {excel_file.sheet_names}"
        )

    df = pd.read_excel(
        excel_file,
        sheet_name=sheet_name,
        dtype=object,
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


def normalize_annual_structure(
    df: pd.DataFrame,
    year: int,
) -> pd.DataFrame:
    """Normaliza una hoja anual del nuevo archivo."""
    expected = required_columns_for_year(year)
    missing = set(expected.values()) - set(df.columns)

    if missing:
        raise ValueError(
            f"La hoja {year} no tiene la estructura esperada. "
            f"Faltan columnas: {sorted(missing)}. "
            f"Columnas disponibles: {list(df.columns)}"
        )

    normalized = pd.DataFrame(
        {
            "year": year,
            "source_row": df.index + 2,

            "component_raw_code": df[expected["component_code"]],
            "component_label": df[expected["component_label"]],
            "component_weight": df[expected["component_weight"]],

            "variable_raw_code": df[expected["variable_code"]],
            "variable_label": df[expected["variable_label"]],
            "variable_weight": df[expected["variable_weight"]],

            "indicator_raw_code": df[expected["indicator_code"]],
            "indicator_label": df[expected["indicator_label"]],
            "indicator_weight": df[expected["indicator_weight"]],
        }
    )

    text_columns = [
        "component_raw_code",
        "component_label",
        "variable_raw_code",
        "variable_label",
        "variable_weight",
        "indicator_raw_code",
        "indicator_label",
        "indicator_weight",
        "component_weight",
    ]

    for column in text_columns:
        normalized[column] = normalized[column].apply(clean_text)

    # Soporta hojas con celdas combinadas o jerarquías no repetidas.
    hierarchy_columns = [
        "component_raw_code",
        "component_label",
        "component_weight",
        "variable_raw_code",
        "variable_label",
        "variable_weight",
        "indicator_raw_code",
        "indicator_label",
        "indicator_weight",
    ]

    normalized[hierarchy_columns] = (
        normalized[hierarchy_columns]
        .ffill()
    )

    # Solo se conservan filas que tienen jerarquía completa.
    normalized = normalized[
        normalized["component_raw_code"].notna()
        & normalized["component_label"].notna()
        & normalized["variable_raw_code"].notna()
        & normalized["variable_label"].notna()
        & normalized["indicator_raw_code"].notna()
        & normalized["indicator_label"].notna()
    ].copy()

    if normalized.empty:
        raise ValueError(
            f"La hoja {year} no produjo registros jerárquicos válidos."
        )

    normalized["component_weight"] = (
        normalized["component_weight"].apply(parse_number)
    )
    normalized["variable_weight"] = (
        normalized["variable_weight"].apply(parse_number)
    )
    normalized["indicator_weight"] = (
        normalized["indicator_weight"].apply(parse_number)
    )

    normalized["component_code"] = (
        normalized["component_raw_code"]
        .apply(lambda value: make_code("C", value))
    )

    normalized["variable_local_code"] = (
        normalized["variable_raw_code"]
        .apply(lambda value: make_code("V", value))
    )

    normalized["indicator_local_code"] = (
        normalized["indicator_raw_code"]
        .apply(lambda value: make_code("I", value))
    )

    # Los códigos jerárquicos evitan colisiones entre niveles.
    normalized["variable_code"] = (
        normalized["component_code"]
        + "_"
        + normalized["variable_local_code"]
    )

    normalized["indicator_code"] = (
        normalized["variable_code"]
        + "_"
        + normalized["indicator_local_code"]
    )

    return normalized


# ---------------------------------------------------------------------
# CONSTRUCCIÓN DE COMPONENTES, VARIABLES E INDICADORES
# ---------------------------------------------------------------------

def validate_repeated_record(
    existing: dict,
    candidate: dict,
    key: tuple,
) -> None:
    """Valida que las filas repetidas sean metodológicamente consistentes."""
    conflicts = []

    if normalize_key(existing["label"]) != normalize_key(candidate["label"]):
        conflicts.append(
            f"label: {existing['label']!r} != {candidate['label']!r}"
        )

    if existing["parent_code"] != candidate["parent_code"]:
        conflicts.append(
            f"parent_code: {existing['parent_code']!r} "
            f"!= {candidate['parent_code']!r}"
        )

    if not numbers_equal(existing["weight"], candidate["weight"]):
        conflicts.append(
            f"weight: {existing['weight']!r} != {candidate['weight']!r}"
        )

    if conflicts:
        raise ValueError(
            "La estructura anual contiene información contradictoria para "
            f"la sección {key}. Fila inicial {existing['source_row']} y "
            f"fila conflictiva {candidate['source_row']}. "
            f"Conflictos: {'; '.join(conflicts)}"
        )


def add_section_record(
    registry: OrderedDict,
    candidate: dict,
) -> None:
    """Agrega una sección o valida que su repetición sea consistente."""
    key = (
        int(candidate["year"]),
        candidate["level"],
        candidate["code"],
    )

    existing = registry.get(key)

    if existing is None:
        registry[key] = candidate
        return

    validate_repeated_record(
        existing=existing,
        candidate=candidate,
        key=key,
    )


def build_section_records(
    normalized: pd.DataFrame,
) -> list[dict]:
    """Construye registros únicos de secciones.

    Las filas de bucles y subpreguntas repiten componentes, variables e
    indicadores. Estas repeticiones son validadas y no generan registros
    adicionales.
    """
    registry = OrderedDict()

    for _, row in normalized.iterrows():
        year = int(row["year"])
        source_row = int(row["source_row"])

        component_record = {
            "year": year,
            "source_sheet": str(year),
            "source_row": source_row,
            "level": "COMPONENTE",
            "code": row["component_code"],
            "raw_code": row["component_raw_code"],
            "parent_code": None,
            "label": row["component_label"],
            "weight": row["component_weight"],
            "display_order": make_display_order(
                row["component_raw_code"]
            ),
        }

        variable_record = {
            "year": year,
            "source_sheet": str(year),
            "source_row": source_row,
            "level": "VARIABLE",
            "code": row["variable_code"],
            "raw_code": row["variable_raw_code"],
            "parent_code": row["component_code"],
            "label": row["variable_label"],
            "weight": row["variable_weight"],
            "display_order": make_display_order(
                row["variable_raw_code"]
            ),
        }

        indicator_record = {
            "year": year,
            "source_sheet": str(year),
            "source_row": source_row,
            "level": "INDICADOR",
            "code": row["indicator_code"],
            "raw_code": row["indicator_raw_code"],
            "parent_code": row["variable_code"],
            "label": row["indicator_label"],
            "weight": row["indicator_weight"],
            "display_order": make_display_order(
                row["indicator_raw_code"]
            ),
        }

        add_section_record(registry, component_record)
        add_section_record(registry, variable_record)
        add_section_record(registry, indicator_record)

    records = list(registry.values())

    records.sort(
        key=lambda item: (
            int(item["year"]),
            LEVEL_ORDER[item["level"]],
            int(item["display_order"]),
            item["code"],
        )
    )

    return records


# ---------------------------------------------------------------------
# HELPER, LABEL Y DESCRIPTION
# ---------------------------------------------------------------------

def make_helper(record: dict) -> str:
    """Construye el helper técnico para trazabilidad y actualizaciones."""
    helper = {
        "source": CURRENT_SOURCE_NAME,
        "source_sheet": record["source_sheet"],
        "source_row": record["source_row"],
        "source_version": 2,
        "entity": "forms.sections",
        "year": record["year"],
        "level": record["level"],
        "code": record["code"],
        "raw_code": record["raw_code"],
        "parent_code": record["parent_code"],
        "weight": record["weight"],
        "label_full": record["label"],
        "natural_key": (
            f"{record['year']}|"
            f"{record['level']}|"
            f"{record['code']}"
        ),
    }

    return json.dumps(
        helper,
        ensure_ascii=False,
        sort_keys=True,
    )


def make_description(record: dict) -> str:
    """Construye una descripción sin perder el nombre completo."""
    weight_label = WEIGHT_SOURCE_COLUMN[record["level"]]

    weight_text = (
        "sin ponderación registrada"
        if record["weight"] is None
        else f"{weight_label}: {record['weight']}"
    )

    return (
        f"{record['label']} "
        f"[{record['level'].capitalize()} del Índice de Innovación Pública "
        f"{record['year']}; código fuente: {record['raw_code']}; "
        f"{weight_text}]."
    )


# ---------------------------------------------------------------------
# CONSULTAS A POSTGRESQL
# ---------------------------------------------------------------------

async def get_table_columns(conn) -> dict:
    """Consulta la definición real de forms.sections."""
    query = text(
        """
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'forms'
          AND table_name = 'sections'
        ORDER BY ordinal_position;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    if not rows:
        raise ValueError(
            "No se encontró la tabla forms.sections en PostgreSQL."
        )

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_required_db_columns(db_columns: dict) -> None:
    """Valida las columnas necesarias para la carga."""
    required = {
        "id",
        "form_id",
        "file_id",
        "parent_id",
        "section_type_id",
        "label",
        "description",
        "helper",
        "display_order",
    }

    missing = required - set(db_columns)

    if missing:
        raise ValueError(
            "La tabla forms.sections no tiene todas las columnas requeridas. "
            f"Faltan: {sorted(missing)}"
        )


async def get_forms_lookup(
    conn,
    active_years: tuple[int, ...],
) -> dict[int, str]:
    """Obtiene el form_id correspondiente a cada año."""
    query = text(
        """
        SELECT
            anno,
            id::text AS id
        FROM forms.forms
        ORDER BY anno;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    grouped = {}

    for row in rows:
        year = int(row["anno"])

        if year not in active_years:
            continue

        grouped.setdefault(year, []).append(row["id"])

    lookup = {}

    for year in active_years:
        ids = grouped.get(year, [])

        if not ids:
            raise ValueError(
                f"No existe formulario para el año {year} en forms.forms."
            )

        if len(ids) > 1:
            raise ValueError(
                f"Existen {len(ids)} formularios para el año {year}. "
                "Debe existir exactamente uno."
            )

        form_id = ids[0]

        if not is_uuidv7(form_id):
            raise ValueError(
                f"El form_id del año {year} no es UUIDv7: {form_id}"
            )

        lookup[year] = form_id

    return lookup


async def get_section_types_lookup(conn) -> dict[str, str]:
    """Obtiene los IDs de COMPONENTE, VARIABLE e INDICADOR."""
    query = text(
        """
        SELECT
            UPPER(TRIM(label)) AS label,
            id::text AS id
        FROM forms.section_types;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    grouped = {}

    for row in rows:
        label = clean_text(row["label"])

        if label not in SECTION_LEVELS:
            continue

        grouped.setdefault(label, []).append(row["id"])

    lookup = {}

    for level in SECTION_LEVELS:
        ids = grouped.get(level, [])

        if not ids:
            raise ValueError(
                f"No existe el tipo de sección {level}."
            )

        if len(ids) > 1:
            raise ValueError(
                f"Existen varios section_types con label {level}: {ids}"
            )

        section_type_id = ids[0]

        if not is_uuidv7(section_type_id):
            raise ValueError(
                f"El section_type_id de {level} no es UUIDv7: "
                f"{section_type_id}"
            )

        lookup[level] = section_type_id

    return lookup


async def get_existing_sections_map(
    conn,
    active_years: tuple[int, ...],
) -> dict[tuple[int, str, str], str]:
    """Obtiene las secciones ya generadas por este proceso.

    Reconoce tanto el nombre anterior como el nuevo del archivo.
    """
    query = text(
        """
        SELECT
            s.id::text AS id,
            f.anno,
            st.label AS section_type,
            s.helper
        FROM forms.sections s
        JOIN forms.forms f
            ON f.id = s.form_id
        LEFT JOIN forms.section_types st
            ON st.id = s.section_type_id
        ORDER BY f.anno, s.id;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    existing = {}

    for row in rows:
        year = int(row["anno"])

        if year not in active_years:
            continue

        helper = parse_helper(row["helper"])

        if not is_managed_helper(helper):
            continue

        helper_year = int(helper.get("year"))
        helper_level = str(helper.get("level"))
        helper_code = str(helper.get("code"))

        if helper_year != year:
            raise ValueError(
                "Se encontró una sección cuyo año del helper no coincide "
                f"con el formulario. ID: {row['id']}; "
                f"formulario: {year}; helper: {helper_year}."
            )

        database_type = clean_text(row["section_type"])

        if database_type and database_type != helper_level:
            raise ValueError(
                "Se encontró una sección cuyo section_type no coincide "
                f"con el helper. ID: {row['id']}; "
                f"section_type: {database_type}; "
                f"helper level: {helper_level}."
            )

        key = (
            helper_year,
            helper_level,
            helper_code,
        )

        if key in existing:
            raise ValueError(
                f"Hay secciones duplicadas para la llave {key}: "
                f"{existing[key]} y {row['id']}."
            )

        if not is_uuidv7(row["id"]):
            raise ValueError(
                f"La sección existente {key} no tiene UUIDv7: {row['id']}"
            )

        existing[key] = row["id"]

    return existing


# ---------------------------------------------------------------------
# PREPARACIÓN E INSERCIÓN
# ---------------------------------------------------------------------

def prepare_db_record(
    source_record: dict,
    db_columns: dict,
    form_id: str,
    section_type_id: str,
    parent_id: str | None,
    existing_id: str | None,
) -> dict:
    """Prepara una sección para INSERT o UPDATE."""
    full_label = clean_text(source_record["label"])

    if full_label is None:
        raise ValueError(
            f"Se encontró una sección sin label: {source_record}"
        )

    label_max_length = db_columns["label"]["max_length"]

    if (
        label_max_length is not None
        and len(full_label) > label_max_length
    ):
        logger.warning(
            f"El label completo de {source_record['year']} "
            f"{source_record['level']} {source_record['code']} tiene "
            f"{len(full_label)} caracteres y será recortado a "
            f"{label_max_length}. El texto completo queda en description "
            "y helper."
        )

    label = truncate_text(
        full_label,
        label_max_length,
    )

    description = make_description(source_record)
    description = truncate_text(
        description,
        db_columns["description"]["max_length"],
    )

    if (
        description is None
        and not db_columns["description"]["nullable"]
    ):
        description = full_label

    helper = make_helper(source_record)
    helper = truncate_text(
        helper,
        db_columns["helper"]["max_length"],
    )

    section_id = existing_id or new_uuidv7()

    if not is_uuidv7(section_id):
        raise ValueError(
            f"El ID preparado para la sección no es UUIDv7: {section_id}"
        )

    return {
        "id": section_id,
        "form_id": form_id,
        "file_id": None,
        "parent_id": parent_id,
        "section_type_id": section_type_id,
        "label": label,
        "description": description,
        "helper": helper,
        "display_order": int(
            source_record["display_order"] or 0
        ),
    }


async def insert_section(conn, record: dict) -> None:
    """Inserta una sección nueva."""
    query = text(
        """
        INSERT INTO forms.sections (
            id,
            form_id,
            file_id,
            parent_id,
            section_type_id,
            label,
            description,
            helper,
            display_order
        )
        VALUES (
            CAST(:id AS uuid),
            CAST(:form_id AS uuid),
            CAST(:file_id AS uuid),
            CAST(:parent_id AS uuid),
            CAST(:section_type_id AS uuid),
            :label,
            :description,
            :helper,
            :display_order
        );
        """
    )

    await conn.execute(query, record)


async def update_section(conn, record: dict) -> None:
    """Actualiza una sección conservando su UUID."""
    query = text(
        """
        UPDATE forms.sections
        SET
            form_id = CAST(:form_id AS uuid),
            file_id = CAST(:file_id AS uuid),
            parent_id = CAST(:parent_id AS uuid),
            section_type_id = CAST(:section_type_id AS uuid),
            label = :label,
            description = :description,
            helper = :helper,
            display_order = :display_order
        WHERE id = CAST(:id AS uuid);
        """
    )

    await conn.execute(query, record)


# ---------------------------------------------------------------------
# VALIDACIONES POSTERIORES
# ---------------------------------------------------------------------

async def validate_loaded_sections(
    conn,
    active_years: tuple[int, ...],
    expected_records: list[dict],
) -> None:
    """Valida UUIDv7, relaciones y jerarquía."""
    expected_by_key = {
        (
            int(record["year"]),
            record["level"],
            record["code"],
        ): record
        for record in expected_records
    }

    query = text(
        """
        SELECT
            child.id::text AS id,
            child.form_id::text AS form_id,
            child.parent_id::text AS parent_id,
            child.helper,
            child.label,
            form_child.anno,
            type_child.label AS section_type,

            parent.id::text AS parent_real_id,
            parent.form_id::text AS parent_form_id,
            parent.helper AS parent_helper,
            type_parent.label AS parent_section_type

        FROM forms.sections child

        JOIN forms.forms form_child
            ON form_child.id = child.form_id

        LEFT JOIN forms.section_types type_child
            ON type_child.id = child.section_type_id

        LEFT JOIN forms.sections parent
            ON parent.id = child.parent_id

        LEFT JOIN forms.section_types type_parent
            ON type_parent.id = parent.section_type_id

        ORDER BY form_child.anno, child.id;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    loaded_by_key = {}

    for row in rows:
        year = int(row["anno"])

        if year not in active_years:
            continue

        helper = parse_helper(row["helper"])

        if not is_managed_helper(helper):
            continue

        key = (
            int(helper["year"]),
            str(helper["level"]),
            str(helper["code"]),
        )

        if key not in expected_by_key:
            continue

        if key in loaded_by_key:
            raise ValueError(
                f"La sección {key} aparece más de una vez en PostgreSQL."
            )

        loaded_by_key[key] = row

    missing_keys = set(expected_by_key) - set(loaded_by_key)

    if missing_keys:
        raise ValueError(
            "No se cargaron todas las secciones esperadas. "
            f"Faltan: {sorted(missing_keys)[:20]}"
        )

    for key, expected in expected_by_key.items():
        row = loaded_by_key[key]
        section_id = row["id"]

        if not is_uuidv7(section_id):
            raise ValueError(
                f"La sección {key} no tiene UUIDv7: {section_id}"
            )

        real_level = clean_text(row["section_type"])

        if real_level != expected["level"]:
            raise ValueError(
                f"La sección {key} tiene section_type={real_level}, "
                f"pero se esperaba {expected['level']}."
            )

        expected_parent_level = PARENT_LEVEL[expected["level"]]

        if expected_parent_level is None:
            if row["parent_id"] is not None:
                raise ValueError(
                    f"El COMPONENTE {key} debería tener parent_id=NULL, "
                    f"pero tiene {row['parent_id']}."
                )

            continue

        if row["parent_id"] is None:
            raise ValueError(
                f"La sección {key} debería tener parent_id."
            )

        if row["parent_real_id"] is None:
            raise ValueError(
                f"La sección {key} apunta a un parent_id inexistente: "
                f"{row['parent_id']}."
            )

        if row["form_id"] != row["parent_form_id"]:
            raise ValueError(
                f"La sección {key} y su padre pertenecen a formularios "
                "diferentes."
            )

        if row["parent_section_type"] != expected_parent_level:
            raise ValueError(
                f"La sección {key} debería depender de "
                f"{expected_parent_level}, pero depende de "
                f"{row['parent_section_type']}."
            )

        parent_helper = parse_helper(row["parent_helper"])

        if not is_managed_helper(parent_helper):
            raise ValueError(
                f"El padre de la sección {key} no tiene un helper "
                "administrado por este proceso."
            )

        expected_parent_key = (
            expected["year"],
            expected_parent_level,
            expected["parent_code"],
        )

        real_parent_key = (
            int(parent_helper["year"]),
            str(parent_helper["level"]),
            str(parent_helper["code"]),
        )

        if real_parent_key != expected_parent_key:
            raise ValueError(
                f"La sección {key} apunta al padre {real_parent_key}, "
                f"pero se esperaba {expected_parent_key}."
            )

    logger.info(
        "forms.sections validation passed successfully. "
        f"Validated sections: {len(expected_by_key)}."
    )


# ---------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------------------------------------------------

async def upgrade(gh, api) -> None:
    """Carga forms.sections desde el nuevo archivo local."""
    del gh
    del api

    logger.info("Starting forms.sections population...")

    path = Path(LOCAL_IIP_STRUCTURE_FILE)
    active_years = get_active_years()

    logger.info(f"IIP structure file: {path}")
    logger.info(f"Active years for sections: {active_years}")

    if not path.exists():
        raise FileNotFoundError(
            f"No existe el archivo local: {path}"
        )

    try:
        excel_file = pd.ExcelFile(path)

        all_records = []

        for year in active_years:
            df_year = read_structure_sheet(
                excel_file=excel_file,
                year=year,
            )

            normalized = normalize_annual_structure(
                df=df_year,
                year=year,
            )

            year_records = build_section_records(normalized)

            if not year_records:
                raise ValueError(
                    f"No se generaron secciones para el año {year}."
                )

            all_records.extend(year_records)

            level_counts = {
                level: sum(
                    1
                    for record in year_records
                    if record["level"] == level
                )
                for level in SECTION_LEVELS
            }

            logger.info(
                f"Year {year}: "
                f"{level_counts['COMPONENTE']} componentes, "
                f"{level_counts['VARIABLE']} variables, "
                f"{level_counts['INDICADOR']} indicadores."
            )

        source_keys = {
            (
                int(record["year"]),
                record["level"],
                record["code"],
            )
            for record in all_records
        }

        async with async_engine.begin() as conn:
            db_columns = await get_table_columns(conn)
            validate_required_db_columns(db_columns)

            forms_lookup = await get_forms_lookup(
                conn=conn,
                active_years=active_years,
            )

            section_types_lookup = (
                await get_section_types_lookup(conn)
            )

            existing_sections = await get_existing_sections_map(
                conn=conn,
                active_years=active_years,
            )

            stale_keys = set(existing_sections) - source_keys

            if stale_keys:
                logger.warning(
                    "Existen secciones administradas por una versión anterior "
                    "que ya no aparecen en el nuevo Excel. No se eliminan "
                    "automáticamente para evitar romper relaciones. "
                    f"Total: {len(stale_keys)}. "
                    f"Muestra: {sorted(stale_keys)[:15]}"
                )

            inserted = 0
            updated = 0

            # Contiene tanto IDs existentes como los recién creados.
            section_id_by_key = dict(existing_sections)

            # El orden es obligatorio para construir parent_id correctamente.
            for level in SECTION_LEVELS:
                level_records = [
                    record
                    for record in all_records
                    if record["level"] == level
                ]

                for source_record in level_records:
                    year = int(source_record["year"])

                    key = (
                        year,
                        source_record["level"],
                        source_record["code"],
                    )

                    parent_id = None

                    if source_record["parent_code"] is not None:
                        parent_level = PARENT_LEVEL[level]

                        parent_key = (
                            year,
                            parent_level,
                            source_record["parent_code"],
                        )

                        parent_id = section_id_by_key.get(parent_key)

                        if parent_id is None:
                            raise ValueError(
                                "No se encontró el parent_id requerido. "
                                f"Sección: {key}. "
                                f"Padre esperado: {parent_key}."
                            )

                    existing_id = existing_sections.get(key)

                    db_record = prepare_db_record(
                        source_record=source_record,
                        db_columns=db_columns,
                        form_id=forms_lookup[year],
                        section_type_id=section_types_lookup[level],
                        parent_id=parent_id,
                        existing_id=existing_id,
                    )

                    if existing_id:
                        await update_section(
                            conn=conn,
                            record=db_record,
                        )
                        updated += 1
                    else:
                        await insert_section(
                            conn=conn,
                            record=db_record,
                        )
                        inserted += 1

                    section_id_by_key[key] = db_record["id"]

            await validate_loaded_sections(
                conn=conn,
                active_years=active_years,
                expected_records=all_records,
            )

        logger.info(
            "forms.sections population finished successfully. "
            f"Inserted: {inserted}. "
            f"Updated: {updated}. "
            f"Active years: {list(active_years)}."
        )

    except Exception as exc:
        logger.exception(
            f"Failed to run forms.sections population: {exc}"
        )
        raise