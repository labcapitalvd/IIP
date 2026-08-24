"""Puebla ``actors.actor_segments`` desde la fuente única ``Entidades.csv``.

Fuente local predeterminada:
    /api/populator/pops/jhonatan/Entidades.csv

Columnas de la fuente utilizadas:
    sector              -> actors.actor_segments.label
    descripcion_sector  -> actors.actor_segments.description
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path

from shared.infrastructure import async_engine
from shared.models import ActorSegment  # Modelo importado correctamente
from shared.utils.logger import get_logger
from shared.utils.seeding import (
    assert_field_lengths,
    clean_text,
    fold_for_comparison,
    generate_technical_slug,
    get_table_columns,
    is_uuidv7,
    load_normalized_csv,
    new_uuidv7,
    validate_required_columns,
)
from sqlalchemy import insert, select, update

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

HEADER_ALIASES = {
    "actorsegmentid": "actor_segment_id",
    "actor_segmentid": "actor_segment_id",
    "descripcionsector": "descripcion_sector",
    "description_sector": "descripcion_sector",
}


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

        sector_key = fold_for_comparison(sector)

        if sector is None:
            raise ValueError(f"Fila {line_number}: sector vacío.")
        if description is None:
            raise ValueError(
                f"Fila {line_number}: descripcion_sector vacía para {sector!r}."
            )
        if legacy_id is None:
            raise ValueError(
                f"Fila {line_number}: actor_segment_id inválido para {sector!r}: {legacy_id!r}."
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


async def get_existing_segments(conn) -> dict[str, dict[str, str]]:
    """Obtiene los segmentos existentes usando consultas de selección limpias."""
    stmt = select(
        ActorSegment.id.label("id"),
        ActorSegment.label.label("label"),
        ActorSegment.description.label("description"),
    ).order_by(ActorSegment.label, ActorSegment.id)

    result = await conn.execute(stmt)

    lookup: dict[str, dict[str, str]] = {}
    for row in result.mappings().all():
        key = fold_for_comparison(row["label"])

        if key is None:
            raise ValueError(f"Existe un actor_segment con label inválido: {row['id']}")

        if key in lookup:
            raise ValueError(
                "Existen sectores duplicados por label normalizado en PostgreSQL: "
                f"{lookup[key]['label']!r} y {row['label']!r}."
            )

        segment_id_str = str(row["id"])
        if not is_uuidv7(segment_id_str):
            raise ValueError(
                "El sector existente no tiene UUIDv7. Debe corregirse antes de "
                f"continuar: {row['label']!r} -> {segment_id_str}"
            )

        lookup[key] = {
            "id": segment_id_str,
            "label": row["label"],
            "description": row["description"],
        }

    return lookup


async def persist_segments(
    conn,
    records: list[dict[str, str]],
    existing: dict[str, dict[str, str]],
    columns: dict[str, dict[str, object]],
) -> tuple[int, int, list[dict[str, str]]]:
    """Inserta o actualiza los segmentos utilizando constructs ORM (DML habilitado)."""
    inserted = 0
    updated = 0
    expected: list[dict[str, str]] = []
    has_updated_at = "updated_at" in columns

    for source in records:
        previous = existing.get(source["source_key"])
        record_id = previous["id"] if previous else new_uuidv7()
        code_value = generate_technical_slug(source["label"])

        if not is_uuidv7(record_id):
            raise ValueError(f"ID no UUIDv7 preparado para sector: {record_id}")

        if previous:
            # UPDATE basado en ORM
            stmt_update = (
                update(ActorSegment)
                .where(ActorSegment.id == record_id)
                .values(
                    label=source["label"],
                    description=source["description"],
                    code=code_value,
                )
            )
            if has_updated_at:
                stmt_update = stmt_update.values(updated_at=datetime.utcnow())

            await conn.execute(stmt_update)
            updated += 1
        else:
            # INSERT basado en ORM
            values_dict = {
                "id": record_id,
                "label": source["label"],
                "description": source["description"],
                "code": code_value,
            }
            if has_updated_at:
                values_dict["updated_at"] = datetime.utcnow()

            stmt_insert = insert(ActorSegment).values(**values_dict)
            await conn.execute(stmt_insert)
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
    """Valida los datos finales utilizando consultas de selección del ORM."""
    stmt = select(ActorSegment.id, ActorSegment.label, ActorSegment.description)
    result = await conn.execute(stmt)

    loaded: dict[str, dict[str, str]] = {}
    for row in result.mappings().all():
        key = fold_for_comparison(row["label"])
        if key is None:
            continue
        if key in loaded:
            raise ValueError(
                f"Sector duplicado por label normalizado después de cargar: {key}"
            )

        # Guardamos convirtiendo explícitamente el id (UUID) a str
        loaded[key] = {
            "id": str(row["id"]),
            "label": row["label"],
            "description": row["description"],
        }

    missing: list[str] = []
    for record in expected:
        row = loaded.get(record["source_key"])
        if row is None:
            missing.append(record["label"])
            continue
        if row["id"] != str(record["id"]):
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
    logger.debug(f"Starting actor_segments population from {ENTITIES_FILE}")

    source_rows = load_normalized_csv(
        path=ENTITIES_FILE,
        required_columns=SOURCE_REQUIRED_COLUMNS,
        header_aliases=HEADER_ALIASES,
    )

    sector_records = build_sector_records(source_rows)

    async with async_engine.begin() as conn:
        columns = await get_table_columns(conn, schema="actors", table="actor_segments")

        validate_required_columns(
            columns,
            required={"id", "label", "description", "code"},
            table_name="actors.actor_segments",
        )
        assert_field_lengths(sector_records, columns, fields=["label", "description"])

        existing = await get_existing_segments(conn)
        inserted, updated, expected = await persist_segments(
            conn=conn,
            records=sector_records,
            existing=existing,
            columns=columns,
        )
        await validate_loaded_segments(conn, expected)
        logger.debug(
            "actor_segments population finished successfully. "
            f"Inserted={inserted}; updated={updated}; total_source={len(expected)}."
        )


if __name__ == "main":
    asyncio.run(upgrade())
