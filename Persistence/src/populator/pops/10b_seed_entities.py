"""Puebla ``actors.actors`` desde la fuente única ``Entidades.csv``.

Fuente local predeterminada:
    /api/populator/pops/jhonatan/Entidades.csv

Asignación de columnas:
    sector              -> se usa para resolver actors.actors.actor_segment_id
    label               -> actors.actors.label
    description         -> actors.actors.description
    mission             -> actors.actors.mission
    vision              -> actors.actors.vision
    sigep_code          -> actors.actors.sigep_code, si la columna existe
    treasury_code       -> actors.actors.treasury_code, si la columna existe
    initials            -> actors.actors.initials, si la columna existe

Columnas de control de calidad, no insertadas directamente:
    id                  -> UUID legado de la entidad en la fuente
    actor_segment_id    -> UUID legado del sector en la fuente
    descripcion_sector  -> se carga mediante 10a_seed_sectors.py

Criterios de población:
    - La FK actor_segment_id se resuelve con el UUIDv7 real del sector en
      PostgreSQL, usando el label de ``sector``.
    - Los UUIDv4 de la fuente no se copian. Los registros nuevos reciben UUIDv7.
    - Si una entidad ya existe, conserva su UUIDv7 y se actualiza desde la
      fuente oficial.
    - La idempotencia se basa en el label normalizado de la entidad.
    - Los códigos SIGEP y de Tesorería se tratan como identificadores, no como
      medidas. Se preservan como texto cuando la columna destino es textual.
    - Los valores ausentes de sigep_code, treasury_code e initials quedan NULL;
      no se inventan códigos ni siglas.
    - contact_person_id no proviene de la fuente y no se modifica.
    - No se eliminan entidades adicionales existentes en PostgreSQL.
    - No se utiliza helper ni se depende de la API HTTP.

Importante:
    La versión base del modelo del proyecto solo contiene actor_segment_id,
    contact_person_id, label, description, mission, vision e id. Para conservar
    toda la fuente, la tabla debe incluir sigep_code, treasury_code e initials.
    Por defecto este script exige esas columnas. Para permitir una carga parcial
    en un esquema antiguo puede definirse:
        REQUIRE_EXTENDED_ACTOR_COLUMNS=false
"""

from __future__ import annotations

import asyncio
import csv
import io
import os
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from uuid_utils import uuid7

from shared.infrastructure import async_engine
from shared.utils.logger import get_logger


logger = get_logger(__name__)

ENTITIES_FILE = Path(
    os.getenv(
        "ENTITIES_FILE",
        "/api/populator/pops/jhonatan/Entidades.csv",
    )
)

REQUIRE_EXTENDED_ACTOR_COLUMNS = os.getenv(
    "REQUIRE_EXTENDED_ACTOR_COLUMNS",
    "true",
).strip().casefold() not in {"0", "false", "no", "off"}

SOURCE_REQUIRED_COLUMNS = {
    "actor_segment_id",
    "sigep_code",
    "treasury_code",
    "initials",
    "label",
    "description",
    "mission",
    "vision",
    "id",
    "sector",
    "descripcion_sector",
}

TARGET_CORE_COLUMNS = {
    "id",
    "actor_segment_id",
    "label",
    "description",
    "mission",
    "vision",
}

TARGET_EXTENDED_COLUMNS = {
    "sigep_code",
    "treasury_code",
    "initials",
}


def clean_text(value: object) -> str | None:
    if value is None:
        return None

    cleaned = str(value).replace("\ufeff", "").strip()
    return cleaned or None


def normalize_key(value: object) -> str | None:
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    normalized = unicodedata.normalize("NFKD", cleaned)
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    normalized = normalized.casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or None


def normalize_column_name(value: object) -> str:
    cleaned = clean_text(value) or ""
    normalized = unicodedata.normalize("NFKD", cleaned)
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    normalized = normalized.casefold().replace("-", " ")
    normalized = re.sub(r"\s+", "_", normalized).strip("_")

    aliases = {
        "actorsegmentid": "actor_segment_id",
        "actor_segmentid": "actor_segment_id",
        "descripcionsector": "descripcion_sector",
        "description_sector": "descripcion_sector",
        "sigepcode": "sigep_code",
        "treasurycode": "treasury_code",
        "treusary_code": "treasury_code",
        "sigla": "initials",
    }
    return aliases.get(normalized, normalized)


def is_uuid(value: object) -> bool:
    cleaned = clean_text(value)
    if cleaned is None:
        return False

    try:
        UUID(cleaned)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def is_uuidv7(value: object) -> bool:
    cleaned = clean_text(value)
    if cleaned is None:
        return False

    try:
        return UUID(cleaned).version == 7
    except (ValueError, TypeError, AttributeError):
        return False


def new_uuidv7() -> str:
    return str(uuid7())


def decode_csv(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo de entidades: {path}")

    raw = path.read_bytes()
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")

    raise ValueError(
        f"No fue posible decodificar {path}. Intentos: {' | '.join(errors)}"
    )


def detect_delimiter(csv_text: str) -> str:
    try:
        return csv.Sniffer().sniff(
            csv_text[:20000], delimiters=";,|\t"
        ).delimiter
    except csv.Error:
        return ";"


def load_source_rows(path: Path) -> list[dict[str, str | None]]:
    csv_text = decode_csv(path)
    delimiter = detect_delimiter(csv_text)
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)

    if reader.fieldnames is None:
        raise ValueError(f"El archivo {path} no contiene encabezados.")

    normalized_headers = [normalize_column_name(name) for name in reader.fieldnames]
    if len(normalized_headers) != len(set(normalized_headers)):
        raise ValueError(
            "El archivo contiene encabezados duplicados después de normalizarlos: "
            f"{normalized_headers}"
        )

    missing = SOURCE_REQUIRED_COLUMNS - set(normalized_headers)
    if missing:
        raise ValueError(
            f"Faltan columnas obligatorias en {path.name}: {sorted(missing)}"
        )

    rows: list[dict[str, str | None]] = []
    for line_number, raw_row in enumerate(reader, start=2):
        row = {
            normalized_headers[index]: clean_text(raw_row.get(original_header))
            for index, original_header in enumerate(reader.fieldnames)
        }
        row["_line_number"] = str(line_number)

        if all(value is None for key, value in row.items() if key != "_line_number"):
            continue
        rows.append(row)

    if not rows:
        raise ValueError(f"El archivo {path} no contiene entidades útiles.")

    return rows


def validate_optional_unique(
    rows: list[dict[str, str | None]],
    column: str,
    normalize: bool = False,
) -> None:
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []

    for row in rows:
        value = clean_text(row.get(column))
        if value is None:
            continue
        key = normalize_key(value) if normalize else value
        if key is None:
            continue

        previous_label = seen.get(key)
        if previous_label is not None:
            duplicates.append((value, previous_label, row["label"] or ""))
        else:
            seen[key] = row["label"] or ""

    if duplicates:
        raise ValueError(
            f"La columna {column} contiene valores duplicados: {duplicates[:20]}"
        )


def validate_and_prepare_source(
    rows: list[dict[str, str | None]],
) -> list[dict[str, str | None]]:
    prepared: list[dict[str, str | None]] = []
    entity_keys: dict[str, str] = {}
    sector_key_to_legacy_id: dict[str, str] = {}
    legacy_segment_id_to_sector_key: dict[str, str] = {}

    for row in rows:
        line_number = row["_line_number"]
        required_values = {
            "sector": clean_text(row.get("sector")),
            "descripcion_sector": clean_text(row.get("descripcion_sector")),
            "label": clean_text(row.get("label")),
            "description": clean_text(row.get("description")),
            "mission": clean_text(row.get("mission")),
            "vision": clean_text(row.get("vision")),
            "id": clean_text(row.get("id")),
            "actor_segment_id": clean_text(row.get("actor_segment_id")),
        }

        missing = [name for name, value in required_values.items() if value is None]
        if missing:
            raise ValueError(
                f"Fila {line_number}: faltan valores obligatorios: {missing}."
            )

        if not is_uuid(required_values["id"]):
            raise ValueError(
                f"Fila {line_number}: id legado inválido: {required_values['id']!r}."
            )
        if not is_uuid(required_values["actor_segment_id"]):
            raise ValueError(
                "Fila "
                f"{line_number}: actor_segment_id legado inválido: "
                f"{required_values['actor_segment_id']!r}."
            )

        entity_key = normalize_key(required_values["label"])
        sector_key = normalize_key(required_values["sector"])
        if entity_key is None or sector_key is None:
            raise ValueError(f"Fila {line_number}: label o sector inválido.")

        previous_label = entity_keys.get(entity_key)
        if previous_label is not None:
            raise ValueError(
                "Hay entidades duplicadas por label normalizado: "
                f"{previous_label!r} y {required_values['label']!r}."
            )
        entity_keys[entity_key] = required_values["label"] or ""

        legacy_segment_id = required_values["actor_segment_id"] or ""
        previous_legacy_id = sector_key_to_legacy_id.get(sector_key)
        if previous_legacy_id is not None and previous_legacy_id != legacy_segment_id:
            raise ValueError(
                f"El sector {required_values['sector']!r} tiene más de un "
                "actor_segment_id legado."
            )
        sector_key_to_legacy_id[sector_key] = legacy_segment_id

        previous_sector_key = legacy_segment_id_to_sector_key.get(legacy_segment_id)
        if previous_sector_key is not None and previous_sector_key != sector_key:
            raise ValueError(
                f"El actor_segment_id legado {legacy_segment_id} pertenece a más "
                "de un sector."
            )
        legacy_segment_id_to_sector_key[legacy_segment_id] = sector_key

        sigep_code = clean_text(row.get("sigep_code"))
        treasury_code = clean_text(row.get("treasury_code"))
        initials = clean_text(row.get("initials"))

        for column, value in (
            ("sigep_code", sigep_code),
            ("treasury_code", treasury_code),
        ):
            if value is not None and not re.fullmatch(r"\d+", value):
                raise ValueError(
                    f"Fila {line_number}: {column} debe contener solo dígitos; "
                    f"valor={value!r}."
                )

        prepared.append(
            {
                "source_key": entity_key,
                "legacy_id": required_values["id"],
                "legacy_actor_segment_id": legacy_segment_id,
                "sector_key": sector_key,
                "sector": required_values["sector"],
                "label": required_values["label"],
                "description": required_values["description"],
                "mission": required_values["mission"],
                "vision": required_values["vision"],
                "sigep_code": sigep_code,
                "treasury_code": treasury_code,
                "initials": initials,
            }
        )

    validate_optional_unique(prepared, "sigep_code")
    validate_optional_unique(prepared, "treasury_code")
    validate_optional_unique(prepared, "initials", normalize=True)

    return sorted(prepared, key=lambda item: (item["label"] or "").casefold())


async def get_table_columns(conn) -> dict[str, dict[str, object]]:
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                udt_name,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'actors'
              AND table_name = 'actors'
            ORDER BY ordinal_position;
            """
        )
    )
    rows = result.mappings().all()
    if not rows:
        raise ValueError("No existe la tabla actors.actors.")

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "udt_name": row["udt_name"],
            "max_length": row["character_maximum_length"],
            "numeric_precision": row["numeric_precision"],
            "numeric_scale": row["numeric_scale"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_target_columns(columns: dict[str, dict[str, object]]) -> set[str]:
    missing_core = TARGET_CORE_COLUMNS - set(columns)
    if missing_core:
        raise ValueError(
            "actors.actors no tiene todas las columnas principales requeridas. "
            f"Faltan: {sorted(missing_core)}"
        )

    missing_extended = TARGET_EXTENDED_COLUMNS - set(columns)
    if missing_extended:
        message = (
            "La fuente Entidades.csv contiene sigep_code, treasury_code e initials, "
            "pero actors.actors no tiene todas esas columnas. Faltan: "
            f"{sorted(missing_extended)}."
        )
        if REQUIRE_EXTENDED_ACTOR_COLUMNS:
            raise ValueError(
                message
                + " Agrega las columnas mediante el modelo/migración o define "
                "REQUIRE_EXTENDED_ACTOR_COLUMNS=false para una carga parcial."
            )
        logger.warning(message + " Se omitirán únicamente esas columnas.")
        print(f"[10b] ADVERTENCIA: {message}", flush=True)

    return TARGET_EXTENDED_COLUMNS & set(columns)


def coerce_identifier_for_column(
    value: str | None,
    column_metadata: dict[str, object],
    column_name: str,
) -> str | int | Decimal | None:
    """Adapta un código al tipo real de PostgreSQL sin inventar valores."""
    if value is None:
        return None

    data_type = str(column_metadata["data_type"])
    if data_type in {"smallint", "integer", "bigint"}:
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(
                f"{column_name}={value!r} no puede convertirse a entero."
            ) from exc

    if data_type in {"numeric", "decimal", "real", "double precision"}:
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(
                f"{column_name}={value!r} no puede convertirse a número."
            ) from exc

    return value


def validate_lengths(
    records: list[dict[str, str | None]],
    columns: dict[str, dict[str, object]],
    extended_columns: set[str],
) -> None:
    fields = {
        "label",
        "description",
        "mission",
        "vision",
        *extended_columns,
    }

    for field in fields:
        max_length = columns[field]["max_length"]
        if max_length is None:
            continue

        too_long = [
            (record["label"], record.get(field))
            for record in records
            if record.get(field) is not None
            and len(str(record[field])) > int(max_length)
        ]
        if too_long:
            raise ValueError(
                f"Hay valores de {field} que superan {max_length} caracteres. "
                f"Muestra: {too_long[:10]}"
            )


async def get_segments_by_key(conn) -> dict[str, dict[str, str]]:
    result = await conn.execute(
        text(
            """
            SELECT id::text AS id, label, description
            FROM actors.actor_segments
            ORDER BY label, id;
            """
        )
    )

    rows = result.mappings().all()
    if not rows:
        raise ValueError(
            "actors.actor_segments está vacía. Ejecuta primero "
            "10a_seed_sectors.py."
        )

    lookup: dict[str, dict[str, str]] = {}
    for raw_row in rows:
        row = dict(raw_row)
        key = normalize_key(row["label"])
        if key is None:
            raise ValueError(f"Sector con label inválido en DB: {row['id']}")
        if key in lookup:
            raise ValueError(
                f"Sectores duplicados por label normalizado en DB: {key}"
            )
        if not is_uuidv7(row["id"]):
            raise ValueError(
                f"El sector {row['label']!r} no tiene UUIDv7: {row['id']}"
            )
        lookup[key] = row

    return lookup


async def get_existing_actors(
    conn,
    extended_columns: set[str],
) -> dict[str, dict[str, dict[str, object]]]:
    """Construye índices de entidades existentes por códigos oficiales y label.

    Prioridad de cruce posterior:
        1. sigep_code, cuando existe y no es NULL;
        2. treasury_code, cuando existe y no es NULL;
        3. label normalizado.
    """
    selected = ["id::text AS id", "label"]
    if "sigep_code" in extended_columns:
        selected.append("sigep_code")
    if "treasury_code" in extended_columns:
        selected.append("treasury_code")

    result = await conn.execute(
        text(
            f"""
            SELECT {', '.join(selected)}
            FROM actors.actors
            ORDER BY label, id;
            """
        )
    )

    indexes: dict[str, dict[str, dict[str, object]]] = {
        "label": {},
        "sigep_code": {},
        "treasury_code": {},
    }

    for raw_row in result.mappings().all():
        row = dict(raw_row)
        if not is_uuidv7(row["id"]):
            raise ValueError(
                "La entidad existente no tiene UUIDv7. Debe corregirse antes de "
                f"continuar: {row['label']!r} -> {row['id']}"
            )

        label_key = normalize_key(row["label"])
        if label_key is None:
            raise ValueError(f"Entidad con label inválido en DB: {row['id']}")
        if label_key in indexes["label"]:
            raise ValueError(
                f"Entidades duplicadas por label normalizado en DB: {label_key}"
            )
        indexes["label"][label_key] = row

        for column in ("sigep_code", "treasury_code"):
            if column not in extended_columns:
                continue
            value = clean_text(row.get(column))
            if value is None:
                continue
            if value in indexes[column]:
                raise ValueError(
                    f"Entidades duplicadas por {column} en DB: {value}"
                )
            indexes[column][value] = row

    return indexes


def match_existing_actor(
    source: dict[str, object],
    indexes: dict[str, dict[str, dict[str, object]]],
    extended_columns: set[str],
) -> dict[str, object] | None:
    """Localiza una entidad existente sin depender solo de su nombre."""
    candidates: list[tuple[str, dict[str, object]]] = []

    if "sigep_code" in extended_columns:
        sigep_key = clean_text(source.get("sigep_code"))
        if sigep_key is not None and sigep_key in indexes["sigep_code"]:
            candidates.append(("sigep_code", indexes["sigep_code"][sigep_key]))

    if "treasury_code" in extended_columns:
        treasury_key = clean_text(source.get("treasury_code"))
        if treasury_key is not None and treasury_key in indexes["treasury_code"]:
            candidates.append(
                ("treasury_code", indexes["treasury_code"][treasury_key])
            )

    label_key = str(source["source_key"])
    if label_key in indexes["label"]:
        candidates.append(("label", indexes["label"][label_key]))

    if not candidates:
        return None

    ids = {str(candidate[1]["id"]) for candidate in candidates}
    if len(ids) > 1:
        details = [(criterion, row["id"], row["label"]) for criterion, row in candidates]
        raise ValueError(
            "Los criterios de identificación de una entidad apuntan a registros "
            f"distintos. Fuente={source['label']!r}; coincidencias={details}"
        )

    return candidates[0][1]


def resolve_segment_ids(
    records: list[dict[str, str | None]],
    segments: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    resolved: list[dict[str, object]] = []
    missing: list[tuple[str | None, str | None]] = []

    for source in records:
        segment = segments.get(str(source["sector_key"]))
        if segment is None:
            missing.append((source["label"], source["sector"]))
            continue

        resolved.append(
            {
                **source,
                "actor_segment_id": segment["id"],
            }
        )

    if missing:
        raise ValueError(
            "No se encontró el sector real en PostgreSQL para algunas entidades. "
            f"Muestra: {missing[:20]}"
        )

    return resolved


def build_source_values(
    source: dict[str, object],
    columns: dict[str, dict[str, object]],
    extended_columns: set[str],
) -> dict[str, object]:
    values: dict[str, object] = {
        "actor_segment_id": source["actor_segment_id"],
        "label": source["label"],
        "description": source["description"],
        "mission": source["mission"],
        "vision": source["vision"],
    }

    for column in sorted(extended_columns):
        raw_value = source.get(column)
        if column in {"sigep_code", "treasury_code"}:
            values[column] = coerce_identifier_for_column(
                value=clean_text(raw_value),
                column_metadata=columns[column],
                column_name=column,
            )
        else:
            values[column] = clean_text(raw_value)

    return values


async def persist_actors(
    conn,
    records: list[dict[str, object]],
    existing: dict[str, dict[str, dict[str, object]]],
    columns: dict[str, dict[str, object]],
    extended_columns: set[str],
) -> tuple[int, int, list[dict[str, object]]]:
    inserted = 0
    updated = 0
    expected: list[dict[str, object]] = []
    has_updated_at = "updated_at" in columns

    value_columns = [
        "actor_segment_id",
        "label",
        "description",
        "mission",
        "vision",
        *sorted(extended_columns),
    ]

    for source in records:
        previous = match_existing_actor(
            source=source,
            indexes=existing,
            extended_columns=extended_columns,
        )
        record_id = str(previous["id"]) if previous else new_uuidv7()
        if not is_uuidv7(record_id):
            raise ValueError(f"ID no UUIDv7 preparado para entidad: {record_id}")

        values = build_source_values(source, columns, extended_columns)
        params = {"id": record_id, **values}

        if previous:
            assignments = []
            for column in value_columns:
                if column == "actor_segment_id":
                    assignments.append(
                        "actor_segment_id = CAST(:actor_segment_id AS uuid)"
                    )
                else:
                    assignments.append(f"{column} = :{column}")
            if has_updated_at:
                assignments.append("updated_at = NOW()")

            await conn.execute(
                text(
                    f"""
                    UPDATE actors.actors
                    SET {', '.join(assignments)}
                    WHERE id = CAST(:id AS uuid);
                    """
                ),
                params,
            )
            updated += 1
        else:
            insert_columns = ["id", *value_columns]
            insert_values = ["CAST(:id AS uuid)"]
            for column in value_columns:
                if column == "actor_segment_id":
                    insert_values.append("CAST(:actor_segment_id AS uuid)")
                else:
                    insert_values.append(f":{column}")
            if has_updated_at:
                insert_columns.append("updated_at")
                insert_values.append("NOW()")

            await conn.execute(
                text(
                    f"""
                    INSERT INTO actors.actors ({', '.join(insert_columns)})
                    VALUES ({', '.join(insert_values)});
                    """
                ),
                params,
            )
            inserted += 1

        expected.append(
            {
                "id": record_id,
                "source_key": source["source_key"],
                **values,
            }
        )

    return inserted, updated, expected


async def validate_loaded_actors(
    conn,
    expected: list[dict[str, object]],
    extended_columns: set[str],
) -> None:
    selected_columns = [
        "actor.id::text AS id",
        "actor.actor_segment_id::text AS actor_segment_id",
        "actor.label",
        "actor.description",
        "actor.mission",
        "actor.vision",
        *[f"actor.{column}" for column in sorted(extended_columns)],
    ]

    result = await conn.execute(
        text(
            f"""
            SELECT {', '.join(selected_columns)}
            FROM actors.actors AS actor;
            """
        )
    )

    loaded: dict[str, dict[str, object]] = {}
    for raw_row in result.mappings().all():
        row = dict(raw_row)
        key = normalize_key(row["label"])
        if key is None:
            continue
        if key in loaded:
            raise ValueError(
                f"Entidad duplicada por label normalizado después de cargar: {key}"
            )
        loaded[key] = row

    missing: list[str] = []
    comparable_fields = {
        "actor_segment_id",
        "label",
        "description",
        "mission",
        "vision",
        *extended_columns,
    }

    for record in expected:
        key = str(record["source_key"])
        row = loaded.get(key)
        if row is None:
            missing.append(str(record["label"]))
            continue

        if row["id"] != record["id"]:
            raise ValueError(
                f"El UUID cambió inesperadamente para {record['label']!r}."
            )
        if not is_uuidv7(row["id"]):
            raise ValueError(
                f"La entidad {record['label']!r} no quedó con UUIDv7."
            )

        for field in comparable_fields:
            loaded_value = row.get(field)
            expected_value = record.get(field)

            if field in {"sigep_code", "treasury_code"}:
                if loaded_value is None or expected_value is None:
                    loaded_clean = loaded_value
                    expected_clean = expected_value
                elif isinstance(expected_value, (int, Decimal)):
                    try:
                        loaded_clean = Decimal(str(loaded_value))
                        expected_clean = Decimal(str(expected_value))
                    except InvalidOperation as exc:
                        raise ValueError(
                            f"No fue posible comparar {record['label']!r}.{field}."
                        ) from exc
                else:
                    loaded_clean = str(loaded_value)
                    expected_clean = str(expected_value)
            else:
                loaded_clean = clean_text(loaded_value)
                expected_clean = clean_text(expected_value)

            if loaded_clean != expected_clean:
                raise ValueError(
                    f"Valor incorrecto para {record['label']!r}.{field}: "
                    f"SQL={loaded_value!r}; esperado={expected_value!r}."
                )

    if missing:
        raise ValueError(f"No se cargaron las entidades: {missing}")


async def upgrade() -> None:
    """Carga entidades y resuelve sus sectores mediante UUIDv7 reales."""

    logger.info(f"Starting actors population from {ENTITIES_FILE}")
    source_rows = load_source_rows(ENTITIES_FILE)
    prepared = validate_and_prepare_source(source_rows)

    sector_count = len({record["sector_key"] for record in prepared})
    print(
        f"[10b] Fuente={ENTITIES_FILE}; entidades={len(prepared)}; "
        f"sectores_referenciados={sector_count}.",
        flush=True,
    )

    async with async_engine.begin() as conn:
        columns = await get_table_columns(conn)
        extended_columns = validate_target_columns(columns)
        validate_lengths(prepared, columns, extended_columns)

        segments = await get_segments_by_key(conn)
        resolved = resolve_segment_ids(prepared, segments)
        existing = await get_existing_actors(
            conn=conn,
            extended_columns=extended_columns,
        )

        inserted, updated, expected = await persist_actors(
            conn=conn,
            records=resolved,
            existing=existing,
            columns=columns,
            extended_columns=extended_columns,
        )
        await validate_loaded_actors(
            conn=conn,
            expected=expected,
            extended_columns=extended_columns,
        )

    logger.info(
        "actors population finished successfully. "
        f"Inserted={inserted}; updated={updated}; total_source={len(expected)}."
    )
    print(
        f"[10b] OK. Insertados={inserted}; actualizados={updated}; "
        f"entidades_fuente={len(expected)}.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
