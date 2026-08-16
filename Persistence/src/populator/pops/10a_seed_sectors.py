"""Puebla ``actors.actor_segments`` desde la fuente única ``Entidades.csv``.

Fuente local predeterminada:
    /api/populator/pops/jhonatan/Entidades.csv

Columnas de la fuente utilizadas:
    sector              -> actors.actor_segments.label
    descripcion_sector  -> actors.actor_segments.description

Columnas usadas únicamente para control de calidad:
    actor_segment_id    -> identificador legado del sector en la fuente

Criterios de población:
    - Se genera un solo sector por cada valor único de ``sector``.
    - Un sector debe tener una sola descripción y un solo actor_segment_id
      legado en todo el archivo.
    - El actor_segment_id del CSV no se inserta porque la fuente actual usa
      UUIDv4. Los registros nuevos reciben UUIDv7.
    - Si el sector ya existe, se conserva su UUIDv7 y se actualizan label y
      description con la fuente oficial.
    - La idempotencia se basa en el label normalizado del sector.
    - No se eliminan sectores adicionales que ya existan en PostgreSQL.
    - No se utiliza helper ni se depende de la API HTTP.
"""

from __future__ import annotations

import asyncio
import csv
import io
import os
import re
import unicodedata
from pathlib import Path
from uuid import UUID

from shared.infrastructure import async_engine
from shared.utils.logger import get_logger
from sqlalchemy import text
from uuid_utils import uuid7

logger = get_logger(__name__)

ENTITIES_FILE = Path(
    os.getenv(
        "ENTITIES_FILE",
        "/api/populator/pops/jhonatan/Entidades.csv",
    )
)

SOURCE_REQUIRED_COLUMNS = {
    "actor_segment_id",
    "sector",
    "descripcion_sector",
}


def clean_text(value: object) -> str | None:
    """Convierte valores vacíos en ``None`` sin alterar el contenido interno."""
    if value is None:
        return None

    cleaned = str(value).replace("\ufeff", "").strip()
    return cleaned or None


def normalize_key(value: object) -> str | None:
    """Crea una llave textual robusta para cruces e idempotencia."""
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    normalized = unicodedata.normalize("NFKD", cleaned)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or None


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


def normalize_column_name(value: object) -> str:
    cleaned = clean_text(value) or ""
    normalized = unicodedata.normalize("NFKD", cleaned)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.casefold().replace("-", " ")
    normalized = re.sub(r"\s+", "_", normalized).strip("_")

    aliases = {
        "actorsegmentid": "actor_segment_id",
        "actor_segmentid": "actor_segment_id",
        "descripcionsector": "descripcion_sector",
        "description_sector": "descripcion_sector",
    }
    return aliases.get(normalized, normalized)


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
    sample = csv_text[:20000]
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,|\t").delimiter
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
        raise ValueError(f"El archivo {path} no contiene registros útiles.")

    return rows


def build_sector_records(
    rows: list[dict[str, str | None]],
) -> list[dict[str, str]]:
    """Deduplica la fuente y valida la relación sector-descripción-ID legado."""
    sectors: dict[str, dict[str, str]] = {}
    legacy_id_to_sector_key: dict[str, str] = {}

    for row in rows:
        line_number = row["_line_number"]
        sector = clean_text(row.get("sector"))
        description = clean_text(row.get("descripcion_sector"))
        legacy_id = clean_text(row.get("actor_segment_id"))
        sector_key = normalize_key(sector)

        if sector is None:
            raise ValueError(f"Fila {line_number}: sector vacío.")
        if description is None:
            raise ValueError(
                f"Fila {line_number}: descripcion_sector vacía para {sector!r}."
            )
        if legacy_id is None or not is_uuid(legacy_id):
            raise ValueError(
                f"Fila {line_number}: actor_segment_id inválido para {sector!r}: "
                f"{legacy_id!r}."
            )
        if sector_key is None:
            raise ValueError(f"Fila {line_number}: sector inválido: {sector!r}.")

        previous_key = legacy_id_to_sector_key.get(legacy_id)
        if previous_key is not None and previous_key != sector_key:
            raise ValueError(
                "El mismo actor_segment_id legado está asociado a dos sectores: "
                f"{legacy_id}."
            )
        legacy_id_to_sector_key[legacy_id] = sector_key

        current = sectors.get(sector_key)
        if current is None:
            sectors[sector_key] = {
                "source_key": sector_key,
                "label": sector,
                "description": description,
                "legacy_actor_segment_id": legacy_id,
            }
            continue

        if current["label"] != sector:
            raise ValueError(
                "Existen variantes distintas del mismo sector normalizado: "
                f"{current['label']!r} y {sector!r}."
            )
        if current["description"] != description:
            raise ValueError(
                f"El sector {sector!r} tiene más de una descripcion_sector."
            )
        if current["legacy_actor_segment_id"] != legacy_id:
            raise ValueError(
                f"El sector {sector!r} tiene más de un actor_segment_id legado."
            )

    return sorted(sectors.values(), key=lambda item: item["label"].casefold())


async def get_table_columns(conn) -> dict[str, dict[str, object]]:
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'actors'
              AND table_name = 'actor_segments'
            ORDER BY ordinal_position;
            """
        )
    )
    rows = result.mappings().all()
    if not rows:
        raise ValueError("No existe la tabla actors.actor_segments.")

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_target_columns(columns: dict[str, dict[str, object]]) -> None:
    required = {"id", "label", "description", "code"}
    missing = required - set(columns)
    if missing:
        raise ValueError(
            "actors.actor_segments no tiene todas las columnas requeridas. "
            f"Faltan: {sorted(missing)}"
        )


def validate_lengths(
    records: list[dict[str, str]],
    columns: dict[str, dict[str, object]],
) -> None:
    for field in ("label", "description"):
        max_length = columns[field]["max_length"]
        if max_length is None:
            continue

        too_long = [
            record[field] for record in records if len(record[field]) > int(max_length)
        ]
        if too_long:
            raise ValueError(
                f"Hay valores de {field} que superan {max_length} caracteres: "
                f"{too_long[:10]}"
            )


async def get_existing_segments(conn) -> dict[str, dict[str, str]]:
    result = await conn.execute(
        text(
            """
            SELECT id::text AS id, label, description
            FROM actors.actor_segments
            ORDER BY label, id;
            """
        )
    )

    lookup: dict[str, dict[str, str]] = {}
    for raw_row in result.mappings().all():
        row = dict(raw_row)
        key = normalize_key(row["label"])
        if key is None:
            raise ValueError(f"Existe un actor_segment con label inválido: {row['id']}")
        if key in lookup:
            raise ValueError(
                "Existen sectores duplicados por label normalizado en PostgreSQL: "
                f"{lookup[key]['label']!r} y {row['label']!r}."
            )
        if not is_uuidv7(row["id"]):
            raise ValueError(
                "El sector existente no tiene UUIDv7. Debe corregirse antes de "
                f"continuar: {row['label']!r} -> {row['id']}"
            )
        lookup[key] = row

    return lookup


async def persist_segments(
    conn,
    records: list[dict[str, str]],
    existing: dict[str, dict[str, str]],
    columns: dict[str, dict[str, object]],
) -> tuple[int, int, list[dict[str, str]]]:
    inserted = 0
    updated = 0
    expected: list[dict[str, str]] = []
    has_updated_at = "updated_at" in columns

    for source in records:
        previous = existing.get(source["source_key"])
        record_id = previous["id"] if previous else new_uuidv7()

        # Usar source_key o una clave normalizada para el campo code
        code_value = source["source_key"]

        if not is_uuidv7(record_id):
            raise ValueError(f"ID no UUIDv7 preparado para sector: {record_id}")

        if previous:
            updated_at_sql = ", updated_at = NOW()" if has_updated_at else ""
            await conn.execute(
                text(
                    f"""
                    UPDATE actors.actor_segments
                    SET label = :label,
                        description = :description,
                        code = :code
                        {updated_at_sql}
                    WHERE id = CAST(:id AS uuid);
                    """
                ),
                {
                    "id": record_id,
                    "label": source["label"],
                    "description": source["description"],
                    "code": code_value,
                },
            )
            updated += 1
        else:
            columns_sql = "id, label, description, code"
            values_sql = "CAST(:id AS uuid), :label, :description, :code"
            if has_updated_at:
                columns_sql += ", updated_at"
                values_sql += ", NOW()"

            await conn.execute(
                text(
                    f"""
                    INSERT INTO actors.actor_segments ({columns_sql})
                    VALUES ({values_sql});
                    """
                ),
                {
                    "id": record_id,
                    "label": source["label"],
                    "description": source["description"],
                    "code": code_value,
                },
            )
            inserted += 1

        expected.append(
            {
                "id": record_id,
                "label": source["label"],
                "description": source["description"],
                "source_key": source["source_key"],
            }
        )

    return inserted, updated, expected


async def validate_loaded_segments(conn, expected: list[dict[str, str]]) -> None:
    result = await conn.execute(
        text(
            """
            SELECT id::text AS id, label, description
            FROM actors.actor_segments;
            """
        )
    )

    loaded: dict[str, dict[str, str]] = {}
    for raw_row in result.mappings().all():
        row = dict(raw_row)
        key = normalize_key(row["label"])
        if key is None:
            continue
        if key in loaded:
            raise ValueError(
                f"Sector duplicado por label normalizado después de cargar: {key}"
            )
        loaded[key] = row

    missing: list[str] = []
    for record in expected:
        row = loaded.get(record["source_key"])
        if row is None:
            missing.append(record["label"])
            continue
        if row["id"] != record["id"]:
            raise ValueError(
                f"El UUID cambió inesperadamente para {record['label']!r}."
            )
        if not is_uuidv7(row["id"]):
            raise ValueError(f"El sector {record['label']!r} no quedó con UUIDv7.")
        if clean_text(row["label"]) != record["label"]:
            raise ValueError(f"Label incorrecto para {record['label']!r}.")
        if clean_text(row["description"]) != record["description"]:
            raise ValueError(f"Descripción incorrecta para {record['label']!r}.")

    if missing:
        raise ValueError(f"No se cargaron los sectores: {missing}")


async def upgrade() -> None:
    """Carga los sectores derivados de ``Entidades.csv``."""

    logger.info(f"Starting actor_segments population from {ENTITIES_FILE}")
    source_rows = load_source_rows(ENTITIES_FILE)
    sector_records = build_sector_records(source_rows)

    print(
        f"[10a] Fuente={ENTITIES_FILE}; filas={len(source_rows)}; "
        f"sectores únicos={len(sector_records)}.",
        flush=True,
    )

    async with async_engine.begin() as conn:
        columns = await get_table_columns(conn)
        validate_target_columns(columns)
        validate_lengths(sector_records, columns)
        existing = await get_existing_segments(conn)
        inserted, updated, expected = await persist_segments(
            conn=conn,
            records=sector_records,
            existing=existing,
            columns=columns,
        )
        await validate_loaded_segments(conn, expected)

    logger.info(
        "actor_segments population finished successfully. "
        f"Inserted={inserted}; updated={updated}; total_source={len(expected)}."
    )
    print(
        f"[10a] OK. Insertados={inserted}; actualizados={updated}; "
        f"sectores_fuente={len(expected)}.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
