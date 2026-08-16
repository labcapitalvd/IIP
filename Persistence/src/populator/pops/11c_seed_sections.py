"""Poblado de forms.sections desde Estructura_IIP.xlsx.

Carga la jerarquía:

    COMPONENTE
        └── VARIABLE
              └── INDICADOR

Convención de almacenamiento:

- label:
    Componente 1, Variable 1, Indicador 1, etc.
- description:
    nombre completo del componente, variable o indicador tomado del Excel.
- helper:
    NULL cuando la columna es nullable; cadena vacía si no lo es.
- file_id:
    NULL.
- Los pesos Maxc, Maxv y Maxi NO se guardan en esta tabla.

El script es idempotente y conserva los UUID existentes. Para migrar registros
creados por versiones anteriores, primero intenta identificarlos mediante el
helper antiguo y luego por label/description y jerarquía.
"""

import asyncio
import json
import os
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from uuid_utils import uuid7

from shared.infrastructure import async_engine
from shared.utils.logger import get_logger


logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------

LOCAL_IIP_STRUCTURE_FILE = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

DEFAULT_ACTIVE_YEARS = (2019, 2021, 2023)
SECTION_LEVELS = ("COMPONENTE", "VARIABLE", "INDICADOR")

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

DISPLAY_PREFIX = {
    "COMPONENTE": "Componente",
    "VARIABLE": "Variable",
    "INDICADOR": "Indicador",
}


# -----------------------------------------------------------------------------
# UTILIDADES
# -----------------------------------------------------------------------------


def get_active_years() -> tuple[int, ...]:
    """Obtiene los años activos desde IIP_ACTIVE_YEARS o usa los predeterminados."""
    raw_value = os.getenv("IIP_ACTIVE_YEARS")

    if not raw_value:
        return DEFAULT_ACTIVE_YEARS

    years: list[int] = []

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
        raise ValueError(f"IIP_ACTIVE_YEARS contiene años duplicados: {years}")

    return tuple(years)


def clean_text(value):
    """Convierte None, NaN y cadenas vacías en None."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    value = str(value).strip()
    return value or None


def normalize_key(value):
    """Normaliza texto para comparaciones, sin alterar el valor almacenado."""
    value = clean_text(value)

    if value is None:
        return None

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character for character in value if not unicodedata.combining(character)
    )
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def extract_code_suffix(value):
    """Extrae la parte numérica completa de un código.

    Ejemplos:
        Componente 1   -> 1
        Variable 2.1   -> 2_1
        Indicador 3,2  -> 3_2
    """
    value = clean_text(value)

    if value is None:
        return None

    match = re.search(r"(\d+(?:[.,]\d+)*)", value)

    if not match:
        return None

    return match.group(1).replace(".", "_").replace(",", "_")


def make_code(prefix: str, raw_code) -> str:
    """Construye un código técnico interno estable: C1, V2, I3, etc."""
    suffix = extract_code_suffix(raw_code)

    if suffix:
        return f"{prefix}{suffix}"

    normalized = normalize_key(raw_code) or "sin_codigo"
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")

    return f"{prefix}{normalized}"


def make_section_label(level: str, raw_code) -> str:
    """Construye el label visible: Componente 1, Variable 1, Indicador 1."""
    suffix = extract_code_suffix(raw_code)

    if suffix:
        readable_suffix = suffix.replace("_", ".")
        return f"{DISPLAY_PREFIX[level]} {readable_suffix}"

    raw_code = clean_text(raw_code)

    if raw_code is None:
        raise ValueError(f"No se pudo construir label para {level}: {raw_code!r}")

    return raw_code


def make_display_order(raw_code) -> int:
    """Genera display_order a partir de la numeración del código."""
    suffix = extract_code_suffix(raw_code)

    if suffix is None:
        return 0

    parts = [int(part) for part in suffix.split("_") if part.isdigit()]

    if not parts:
        return 0

    if len(parts) == 1:
        return parts[0]

    order = parts[0] * 1000 + parts[1]

    for part in parts[2:]:
        order = order * 1000 + part

    return order


def parse_helper(helper_text):
    """Convierte un helper JSON anterior en diccionario."""
    helper_text = clean_text(helper_text)

    if helper_text is None:
        return None

    try:
        parsed = json.loads(helper_text)
    except (json.JSONDecodeError, TypeError):
        return None

    return parsed if isinstance(parsed, dict) else None


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
    return str(uuid7())


def truncate_text(value, max_length):
    value = clean_text(value)

    if value is None or max_length is None:
        return value

    return value[:max_length]


# -----------------------------------------------------------------------------
# LECTURA Y NORMALIZACIÓN DEL EXCEL
# -----------------------------------------------------------------------------


def required_columns_for_year(year: int) -> dict[str, str]:
    return {
        "component_code": "Componente",
        "component_description": f"Componente {year}",
        "variable_code": "Variable",
        "variable_description": f"Variable {year}",
        "indicator_code": "Indicador",
        "indicator_description": f"Indicador {year}",
    }


def read_structure_sheet(excel_file: pd.ExcelFile, year: int) -> pd.DataFrame:
    sheet_name = str(year)

    if sheet_name not in excel_file.sheet_names:
        raise ValueError(
            f"No existe la hoja obligatoria {sheet_name!r}. "
            f"Hojas disponibles: {excel_file.sheet_names}"
        )

    df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=object)
    df.columns = [str(column).strip() for column in df.columns]

    return df


def normalize_annual_structure(df: pd.DataFrame, year: int) -> pd.DataFrame:
    expected = required_columns_for_year(year)
    missing = set(expected.values()) - set(df.columns)

    if missing:
        raise ValueError(
            f"La hoja {year} no contiene las columnas requeridas: "
            f"{sorted(missing)}. Columnas disponibles: {list(df.columns)}"
        )

    normalized = pd.DataFrame(
        {
            "year": year,
            "source_row": df.index + 2,
            "component_raw_code": df[expected["component_code"]],
            "component_description": df[expected["component_description"]],
            "variable_raw_code": df[expected["variable_code"]],
            "variable_description": df[expected["variable_description"]],
            "indicator_raw_code": df[expected["indicator_code"]],
            "indicator_description": df[expected["indicator_description"]],
        }
    )

    hierarchy_columns = [
        "component_raw_code",
        "component_description",
        "variable_raw_code",
        "variable_description",
        "indicator_raw_code",
        "indicator_description",
    ]

    for column in hierarchy_columns:
        normalized[column] = normalized[column].apply(clean_text)

    # Soporta celdas combinadas o valores no repetidos en todas las filas.
    normalized[hierarchy_columns] = normalized[hierarchy_columns].ffill()

    normalized = normalized[
        normalized["component_raw_code"].notna()
        & normalized["component_description"].notna()
        & normalized["variable_raw_code"].notna()
        & normalized["variable_description"].notna()
        & normalized["indicator_raw_code"].notna()
        & normalized["indicator_description"].notna()
    ].copy()

    if normalized.empty:
        raise ValueError(f"La hoja {year} no produjo una jerarquía válida.")

    normalized["component_code"] = normalized["component_raw_code"].apply(
        lambda value: make_code(f"{year}_C", value)
    )
    normalized["variable_local_code"] = normalized["variable_raw_code"].apply(
        lambda value: make_code(f"{year}_V", value)
    )
    normalized["indicator_local_code"] = normalized["indicator_raw_code"].apply(
        lambda value: make_code(f"{year}_I", value)
    )

    normalized["variable_code"] = (
        normalized["component_code"] + "_" + normalized["variable_local_code"]
    )
    normalized["indicator_code"] = (
        normalized["variable_code"] + "_" + normalized["indicator_local_code"]
    )

    return normalized


def validate_repeated_record(existing: dict, candidate: dict, key: tuple) -> None:
    conflicts: list[str] = []

    if normalize_key(existing["label"]) != normalize_key(candidate["label"]):
        conflicts.append(f"label {existing['label']!r} != {candidate['label']!r}")

    if normalize_key(existing["description"]) != normalize_key(
        candidate["description"]
    ):
        conflicts.append("description diferente")

    if existing["parent_code"] != candidate["parent_code"]:
        conflicts.append(
            f"parent_code {existing['parent_code']!r} != {candidate['parent_code']!r}"
        )

    if conflicts:
        raise ValueError(
            f"Información contradictoria para la sección {key}. "
            f"Primera fila: {existing['source_row']}; "
            f"fila conflictiva: {candidate['source_row']}. "
            f"Conflictos: {'; '.join(conflicts)}"
        )


def add_section_record(registry: OrderedDict, candidate: dict) -> None:
    key = (
        int(candidate["year"]),
        candidate["level"],
        candidate["code"],
    )

    existing = registry.get(key)

    if existing is None:
        registry[key] = candidate
        return

    validate_repeated_record(existing, candidate, key)


def build_section_records(normalized: pd.DataFrame) -> list[dict]:
    registry = OrderedDict()

    for _, row in normalized.iterrows():
        year = int(row["year"])
        source_row = int(row["source_row"])

        add_section_record(
            registry,
            {
                "year": year,
                "source_row": source_row,
                "level": "COMPONENTE",
                "code": row["component_code"],
                "parent_code": None,
                "label": make_section_label("COMPONENTE", row["component_raw_code"]),
                "description": row["component_description"],
                "display_order": make_display_order(row["component_raw_code"]),
            },
        )

        add_section_record(
            registry,
            {
                "year": year,
                "source_row": source_row,
                "level": "VARIABLE",
                "code": row["variable_code"],
                "parent_code": row["component_code"],
                "label": make_section_label("VARIABLE", row["variable_raw_code"]),
                "description": row["variable_description"],
                "display_order": make_display_order(row["variable_raw_code"]),
            },
        )

        add_section_record(
            registry,
            {
                "year": year,
                "source_row": source_row,
                "level": "INDICADOR",
                "code": row["indicator_code"],
                "parent_code": row["variable_code"],
                "label": make_section_label("INDICADOR", row["indicator_raw_code"]),
                "description": row["indicator_description"],
                "display_order": make_display_order(row["indicator_raw_code"]),
            },
        )

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


# -----------------------------------------------------------------------------
# POSTGRESQL: METADATOS Y CATÁLOGOS
# -----------------------------------------------------------------------------


async def get_table_columns(conn) -> dict:
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
              AND table_name = 'sections'
            ORDER BY ordinal_position;
            """
        )
    )

    rows = result.mappings().all()

    if not rows:
        raise ValueError("No se encontró la tabla forms.sections.")

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_required_db_columns(db_columns: dict) -> None:
    required = {
        "id",
        "code",
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
            "forms.sections no contiene todas las columnas requeridas. "
            f"Faltan: {sorted(missing)}"
        )


async def get_forms_lookup(
    conn,
    active_years: tuple[int, ...],
) -> dict[int, str]:
    result = await conn.execute(
        text(
            """
            SELECT code, id::text AS id
            FROM forms.forms
            ORDER BY code;
            """
        )
    )

    grouped: dict[int, list[str]] = {}

    for row in result.mappings().all():
        year = int(row["code"])

        if year in active_years:
            grouped.setdefault(year, []).append(row["id"])

    lookup: dict[int, str] = {}

    for year in active_years:
        ids = grouped.get(year, [])

        if len(ids) != 1:
            raise ValueError(
                f"Debe existir exactamente un formulario para {year}; "
                f"se encontraron {len(ids)}."
            )

        if not is_uuidv7(ids[0]):
            raise ValueError(f"El form_id de {year} no es UUIDv7: {ids[0]}")

        lookup[year] = ids[0]

    return lookup


async def get_section_types_lookup(conn) -> dict[str, str]:
    result = await conn.execute(
        text(
            """
            SELECT UPPER(TRIM(label)) AS label, id::text AS id
            FROM forms.section_types;
            """
        )
    )

    grouped: dict[str, list[str]] = {}

    for row in result.mappings().all():
        label = clean_text(row["label"])

        if label in SECTION_LEVELS:
            grouped.setdefault(label, []).append(row["id"])

    lookup: dict[str, str] = {}

    for level in SECTION_LEVELS:
        ids = grouped.get(level, [])

        if len(ids) != 1:
            raise ValueError(
                f"Debe existir exactamente un section_type {level}; "
                f"se encontraron {len(ids)}."
            )

        if not is_uuidv7(ids[0]):
            raise ValueError(f"El section_type_id de {level} no es UUIDv7: {ids[0]}")

        lookup[level] = ids[0]

    return lookup


async def get_existing_sections(conn, active_years: tuple[int, ...]) -> list[dict]:
    result = await conn.execute(
        text(
            """
            SELECT
                s.id::text AS id,
                s.code as section_code,
                s.form_id::text AS form_id,
                s.parent_id::text AS parent_id,
                s.section_type_id::text AS section_type_id,
                s.label,
                s.description,
                s.helper,
                s.display_order,
                f.code,
                UPPER(TRIM(st.label)) AS section_type
            FROM forms.sections s
            JOIN forms.forms f
              ON f.id = s.form_id
            LEFT JOIN forms.section_types st
              ON st.id = s.section_type_id
            ORDER BY f.code, s.id;
            """
        )
    )

    rows = []

    for row in result.mappings().all():
        if row["code"] in active_years:
            rows.append(dict(row))

    return rows


# -----------------------------------------------------------------------------
# IDENTIFICACIÓN DE REGISTROS EXISTENTES SIN DEPENDER DEL HELPER
# -----------------------------------------------------------------------------


def select_unique_candidate(candidates: list[dict], reason: str, source_record: dict):
    if not candidates:
        return None

    if len(candidates) > 1:
        details = [
            {
                "id": candidate["id"],
                "label": candidate["label"],
                "description": candidate["description"],
                "parent_id": candidate["parent_id"],
            }
            for candidate in candidates
        ]

        raise ValueError(
            f"No se pudo identificar de forma única la sección "
            f"{source_record['year']} {source_record['level']} "
            f"{source_record['code']} mediante {reason}. "
            f"Candidatos: {details}"
        )

    return candidates[0]


def find_existing_section(
    source_record: dict,
    form_id: str,
    section_type_id: str,
    parent_id: str | None,
    existing_rows: list[dict],
    used_ids: set[str],
):
    """Busca un registro existente con varias estrategias de compatibilidad."""
    available = [
        row
        for row in existing_rows
        if row["id"] not in used_ids
        and row["form_id"] == form_id
        and row["section_type_id"] == section_type_id
    ]

    # 1. Coincidencia directa por código técnico de sección (ej. '2019_C1')
    code_candidates = [
        row
        for row in available
        if row.get("code") == source_record["code"]
        or row.get("section_code") == source_record["code"]
    ]

    candidate = select_unique_candidate(
        code_candidates,
        "código técnico de sección",
        source_record,
    )

    if candidate:
        return candidate

    # 2. Compatibilidad con el helper de versiones anteriores.
    helper_candidates = []

    for row in available:
        helper = parse_helper(row["helper"])

        if not helper:
            continue

        try:
            helper_year = int(helper.get("year"))
        except (TypeError, ValueError):
            continue

        if (
            helper.get("entity") == "forms.sections"
            and helper_year == int(source_record["year"])
            and str(helper.get("level")) == source_record["level"]
            and str(helper.get("code")) == source_record["code"]
        ):
            helper_candidates.append(row)

    candidate = select_unique_candidate(
        helper_candidates,
        "el helper anterior",
        source_record,
    )

    if candidate:
        return candidate

    normalized_label = normalize_key(source_record["label"])
    normalized_description = normalize_key(source_record["description"])

    # 3. Formato nuevo: label técnico y parent_id correcto.
    candidate = select_unique_candidate(
        [
            row
            for row in available
            if row["parent_id"] == parent_id
            and normalize_key(row["label"]) == normalized_label
        ],
        "label y parent_id",
        source_record,
    )

    if candidate:
        return candidate

    # 4. Formato anterior: el nombre completo estaba en label.
    candidate = select_unique_candidate(
        [
            row
            for row in available
            if row["parent_id"] == parent_id
            and (
                normalize_key(row["label"]) == normalized_description
                or normalize_key(row["description"]) == normalized_description
            )
        ],
        "descripción y parent_id",
        source_record,
    )

    if candidate:
        return candidate

    # 5. Permite reparar un parent_id incorrecto si el label técnico es único.
    candidate = select_unique_candidate(
        [row for row in available if normalize_key(row["label"]) == normalized_label],
        "label técnico único",
        source_record,
    )

    if candidate:
        return candidate

    # 6. Último respaldo para migrar el formato anterior.
    candidate = select_unique_candidate(
        [
            row
            for row in available
            if (
                normalize_key(row["label"]) == normalized_description
                or normalize_key(row["description"]) == normalized_description
            )
        ],
        "nombre completo único",
        source_record,
    )

    return candidate


# -----------------------------------------------------------------------------
# INSERT / UPDATE
# -----------------------------------------------------------------------------


def prepare_db_record(
    source_record: dict,
    db_columns: dict,
    form_id: str,
    section_type_id: str,
    parent_id: str | None,
    existing_id: str | None,
) -> dict:
    code = truncate_text(
        source_record["code"],
        db_columns.get("code", {}).get("max_length"),
    )
    label = truncate_text(
        source_record["label"],
        db_columns["label"]["max_length"],
    )
    description = truncate_text(
        source_record["description"],
        db_columns["description"]["max_length"],
    )

    if code is None:
        raise ValueError(f"Sección sin code: {source_record}")
    if label is None:
        raise ValueError(f"Sección sin label: {source_record}")

    if description is None:
        raise ValueError(f"Sección sin description: {source_record}")

    # NULL es la forma correcta de dejar helper vacío cuando la columna lo permite.
    helper_value = None if db_columns["helper"]["nullable"] else ""

    section_id = existing_id or new_uuidv7()

    if not is_uuidv7(section_id):
        raise ValueError(
            f"El ID de {source_record['year']} {source_record['level']} "
            f"{source_record['code']} no es UUIDv7: {section_id}"
        )

    return {
        "id": section_id,
        "code": code,
        "form_id": form_id,
        "file_id": None,
        "parent_id": parent_id,
        "section_type_id": section_type_id,
        "label": label,
        "description": description,
        "helper": helper_value,
        "display_order": int(source_record["display_order"] or 0),
    }


async def insert_section(conn, record: dict) -> None:
    await conn.execute(
        text(
            """
            INSERT INTO forms.sections (
                id,
                code,
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
                :code,
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
        ),
        record,
    )


async def update_section(conn, record: dict) -> None:
    await conn.execute(
        text(
            """
            UPDATE forms.sections
            SET
                code = :code,
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
        ),
        record,
    )


# -----------------------------------------------------------------------------
# VALIDACIÓN FINAL
# -----------------------------------------------------------------------------


async def validate_loaded_sections(
    conn,
    expected_id_by_key: dict[tuple[int, str, str], str],
    expected_by_key: dict[tuple[int, str, str], dict],
    forms_lookup: dict[int, str],
    section_types_lookup: dict[str, str],
    parent_id_by_key: dict[tuple[int, str, str], str | None],
) -> None:
    result = await conn.execute(
        text(
            """
            SELECT
                id::text AS id,
                code,
                form_id::text AS form_id,
                parent_id::text AS parent_id,
                section_type_id::text AS section_type_id,
                label,
                description,
                helper,
                display_order
            FROM forms.sections;
            """
        )
    )

    rows_by_id = {row["id"]: dict(row) for row in result.mappings().all()}

    for key, expected_id in expected_id_by_key.items():
        expected = expected_by_key[key]
        row = rows_by_id.get(expected_id)

        if row is None:
            raise ValueError(f"No se encontró la sección cargada {key}: {expected_id}")

        if not is_uuidv7(row["id"]):
            raise ValueError(f"La sección {key} no tiene UUIDv7: {row['id']}")

        if row["code"] != expected["code"]:
            raise ValueError(
                f"code incorrecto para {key}: {row['code']!r} != {expected['code']!r}"
            )
        if row["form_id"] != forms_lookup[expected["year"]]:
            raise ValueError(f"form_id incorrecto para {key}")

        if row["section_type_id"] != section_types_lookup[expected["level"]]:
            raise ValueError(f"section_type_id incorrecto para {key}")

        if row["parent_id"] != parent_id_by_key[key]:
            raise ValueError(
                f"parent_id incorrecto para {key}: "
                f"{row['parent_id']} != {parent_id_by_key[key]}"
            )

        if normalize_key(row["label"]) != normalize_key(expected["label"]):
            raise ValueError(
                f"label incorrecto para {key}: "
                f"{row['label']!r} != {expected['label']!r}"
            )

        if normalize_key(row["description"]) != normalize_key(expected["description"]):
            raise ValueError(
                f"description incorrecta para {key}: "
                f"{row['description']!r} != {expected['description']!r}"
            )

        if clean_text(row["helper"]) is not None:
            raise ValueError(
                f"helper debe quedar vacío para {key}, pero contiene: {row['helper']!r}"
            )

        if int(row["display_order"]) != int(expected["display_order"]):
            raise ValueError(f"display_order incorrecto para {key}")

    logger.info(
        "forms.sections validation passed successfully. "
        f"Validated sections: {len(expected_id_by_key)}."
    )


# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------------------------------------------------------


async def upgrade() -> None:

    path = Path(LOCAL_IIP_STRUCTURE_FILE)
    active_years = get_active_years()

    logger.info("Starting forms.sections population...")
    logger.info(f"IIP structure file: {path}")
    logger.info(f"Active years: {active_years}")

    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo local: {path}")

    try:
        excel_file = pd.ExcelFile(path)
        all_records: list[dict] = []

        for year in active_years:
            df_year = read_structure_sheet(excel_file, year)
            normalized = normalize_annual_structure(df_year, year)
            year_records = build_section_records(normalized)

            if not year_records:
                raise ValueError(f"No se generaron secciones para {year}.")

            all_records.extend(year_records)

            counts = {
                level: sum(record["level"] == level for record in year_records)
                for level in SECTION_LEVELS
            }

            logger.info(
                f"Year {year}: "
                f"{counts['COMPONENTE']} componentes, "
                f"{counts['VARIABLE']} variables, "
                f"{counts['INDICADOR']} indicadores."
            )

        expected_by_key = {
            (
                int(record["year"]),
                record["level"],
                record["code"],
            ): record
            for record in all_records
        }

        async with async_engine.begin() as conn:
            db_columns = await get_table_columns(conn)
            validate_required_db_columns(db_columns)

            forms_lookup = await get_forms_lookup(conn, active_years)
            section_types_lookup = await get_section_types_lookup(conn)
            existing_rows = await get_existing_sections(conn, active_years)

            inserted = 0
            updated = 0
            used_existing_ids: set[str] = set()
            section_id_by_key: dict[tuple[int, str, str], str] = {}
            parent_id_by_key: dict[tuple[int, str, str], str | None] = {}

            for level in SECTION_LEVELS:
                level_records = [
                    record for record in all_records if record["level"] == level
                ]

                for source_record in level_records:
                    year = int(source_record["year"])
                    key = (year, level, source_record["code"])

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
                                f"No se encontró el padre {parent_key} "
                                f"para la sección {key}."
                            )

                    existing_row = find_existing_section(
                        source_record=source_record,
                        form_id=forms_lookup[year],
                        section_type_id=section_types_lookup[level],
                        parent_id=parent_id,
                        existing_rows=existing_rows,
                        used_ids=used_existing_ids,
                    )

                    existing_id = existing_row["id"] if existing_row else None

                    db_record = prepare_db_record(
                        source_record=source_record,
                        db_columns=db_columns,
                        form_id=forms_lookup[year],
                        section_type_id=section_types_lookup[level],
                        parent_id=parent_id,
                        existing_id=existing_id,
                    )

                    if existing_id:
                        await update_section(conn, db_record)
                        used_existing_ids.add(existing_id)
                        updated += 1
                    else:
                        await insert_section(conn, db_record)
                        inserted += 1

                    section_id_by_key[key] = db_record["id"]
                    parent_id_by_key[key] = parent_id

            await validate_loaded_sections(
                conn=conn,
                expected_id_by_key=section_id_by_key,
                expected_by_key=expected_by_key,
                forms_lookup=forms_lookup,
                section_types_lookup=section_types_lookup,
                parent_id_by_key=parent_id_by_key,
            )

        logger.info(
            "forms.sections population finished successfully. "
            f"Inserted: {inserted}. Updated: {updated}."
        )

    except Exception as exc:
        logger.exception(f"Failed to run forms.sections population: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(upgrade())
