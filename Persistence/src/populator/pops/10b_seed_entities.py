from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from shared.infrastructure import async_engine
from shared.models import Actor, ActorSegment  # Models loaded cleanly
from shared.utils.logger import getLogger
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_field_lengths,
    assert_no_duplicates,
    cast_to_database_numeric,
    clean_text,
    fold_for_comparison,
    generate_technical_slug,
    get_table_columns,
    load_normalized_csv,
    new_uuidv7,
    validate_required_columns,
)
from sqlalchemy import insert, select, update

logger = getLogger(__name__)

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

HEADER_ALIASES = {
    "actorsegmentid": "actor_segment_id",
    "actor_segmentid": "actor_segment_id",
    "descripcionsector": "descripcion_sector",
    "description_sector": "descripcion_sector",
    "sigepcode": "sigep_code",
    "treasurycode": "treasury_code",
    "treusary_code": "treasury_code",
    "sigla": "initials",
}

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
    "code",
}

TARGET_EXTENDED_COLUMNS = {
    "sigep_code",
    "treasury_code",
    "initials",
}


def validate_and_prepare_source(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validates structural integrity constraints and prepares source records."""
    prepared: list[dict[str, Any]] = []

    assert_no_duplicates(
        rows, key_fields=["label"], what="entidades por columna 'label'"
    )
    assert_no_duplicates(
        rows, key_fields=["id"], what="identificadores 'id' de la fuente"
    )

    for row in rows:
        line_number = row["_line_number"]

        required_fields = [
            "sector",
            "descripcion_sector",
            "label",
            "description",
            "mission",
            "vision",
            "id",
            "actor_segment_id",
        ]
        missing = [f for f in required_fields if row.get(f) is None]
        if missing:
            raise ValueError(
                f"Fila {line_number}: faltan valores obligatorios: {missing}."
            )

        entity_key = fold_for_comparison(row["label"])
        sector_key = fold_for_comparison(row["sector"])
        if not entity_key or not sector_key:
            raise ValueError(f"Fila {line_number}: label o sector inválido.")

        sigep_code = clean_text(row.get("sigep_code"))
        treasury_code = clean_text(row.get("treasury_code"))
        initials = clean_text(row.get("initials"))

        for col_name, val in (
            ("sigep_code", sigep_code),
            ("treasury_code", treasury_code),
        ):
            if val is not None and not str(val).isdigit():
                raise ValueError(
                    f"Fila {line_number}: {col_name} debe contener solo dígitos; valor={val!r}."
                )

        prepared.append(
            {
                "source_key": entity_key,
                "code": generate_technical_slug(row["label"]),
                "legacy_id": row["id"],
                "legacy_actor_segment_id": row["actor_segment_id"],
                "sector_key": sector_key,
                "sector": row["sector"],
                "label": row["label"],
                "description": row["description"],
                "mission": row["mission"],
                "vision": row["vision"],
                "sigep_code": sigep_code,
                "treasury_code": treasury_code,
                "initials": initials,
                "_line_number": line_number,
            }
        )

    assert_no_duplicates(
        [p for p in prepared if p.get("sigep_code") is not None],
        key_fields=["sigep_code"],
        what="sigep_code únicos",
    )
    assert_no_duplicates(
        [p for p in prepared if p.get("treasury_code") is not None],
        key_fields=["treasury_code"],
        what="treasury_code únicos",
    )
    assert_no_duplicates(
        [p for p in prepared if p.get("initials") is not None],
        key_fields=["initials"],
        what="initials únicas",
    )

    return sorted(prepared, key=lambda item: str(item["label"]).casefold())


def validate_target_columns(columns: Mapping[str, Any]) -> set[str]:
    """Inspects target catalog fields and ensures minimum requirements are fulfilled."""
    validate_required_columns(columns, TARGET_CORE_COLUMNS, table_name="actors.actors")

    missing_extended = TARGET_EXTENDED_COLUMNS - set(columns.keys())
    if missing_extended:
        message = (
            "La fuente Entidades.csv contiene sigep_code, treasury_code e initials, "
            f"pero actors.actors no tiene todas esas columnas. Faltan: {sorted(missing_extended)}."
        )
        if REQUIRE_EXTENDED_ACTOR_COLUMNS:
            raise ValueError(
                f"{message} Agrega las columnas mediante el modelo/migración o define "
                "REQUIRE_EXTENDED_ACTOR_COLUMNS=false para una carga parcial."
            )
        logger.warning(f"{message} Se omitirán únicamente esas columnas.")
        print(f"[10b] ADVERTENCIA: {message}", flush=True)

    return TARGET_EXTENDED_COLUMNS & set(columns.keys())


async def get_segments_by_key(conn) -> dict[str, dict[str, Any]]:
    """Builds a case-insensitive normalized lookup map for upstream sector segments using explicit structural mappings."""
    stmt = select(
        ActorSegment.id.label("id"),
        ActorSegment.label.label("label"),
        ActorSegment.description.label("description"),
    ).order_by(ActorSegment.label, ActorSegment.id)

    result = await conn.execute(stmt)
    mapped_rows = result.mappings().all()

    if not mapped_rows:
        raise ValueError(
            "actors.actor_segments está vacía. Ejecuta primero 10a_seed_sectors.py."
        )

    rows = [
        {"id": str(row["id"]), "label": row["label"], "description": row["description"]}
        for row in mapped_rows
    ]
    assert_all_uuidv7(rows, id_key="id", label_key="label")

    lookup: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = fold_for_comparison(row["label"])
        if not key:
            raise ValueError(f"Sector con label inválido en DB: {row['id']}")
        if key in lookup:
            raise ValueError(f"Sectores duplicados por label normalizado en DB: {key}")
        lookup[key] = row

    return lookup


async def get_existing_actors(
    conn, extended_columns: set[str]
) -> dict[str, dict[str, Any]]:
    """Fetches already persisted entities into standardized indexing grids using explicit mapping targets."""
    columns_to_select = [Actor.id.label("id"), Actor.label.label("label")]

    for col in sorted(extended_columns):
        if hasattr(Actor, col):
            columns_to_select.append(getattr(Actor, col).label(col))

    stmt = select(*columns_to_select).order_by(Actor.label, Actor.id)
    result = await conn.execute(stmt)

    rows: list[dict[str, Any]] = []
    for row in result.mappings().all():
        record = {
            "id": str(row["id"]),
            "label": row["label"],
        }

        for col in sorted(extended_columns):
            if col in row:
                record[col] = row[col]

        rows.append(record)

    assert_all_uuidv7(rows, id_key="id", label_key="label")

    indexes: dict[str, dict[str, Any]] = {
        "label": {},
        "sigep_code": {},
        "treasury_code": {},
    }

    # FIX: Iterate directly over the clean records list instead of the DB row proxy mapping
    for record in rows:
        label_key = fold_for_comparison(record["label"])
        if label_key:
            if label_key in indexes["label"]:
                raise ValueError(
                    f"Entidades duplicadas por label normalizado en DB: {label_key}"
                )
            indexes["label"][label_key] = record

        for column in ("sigep_code", "treasury_code"):
            if column not in record:
                continue
            val = clean_text(record[column])
            if val is not None:
                if val in indexes[column]:
                    raise ValueError(f"Entidades duplicadas por {column} en DB: {val}")
                indexes[column][val] = record

    return indexes


def match_existing_actor(
    source: dict[str, Any],
    indexes: dict[str, dict[str, Any]],
    extended_columns: set[str],
) -> dict[str, Any] | None:
    """Matches a source record with an existing database entry using prioritized unique constraints."""
    candidates: list[tuple[str, dict[str, Any]]] = []

    if "sigep_code" in extended_columns and source.get("sigep_code") is not None:
        val = clean_text(source["sigep_code"])
        if val in indexes["sigep_code"]:
            candidates.append(("sigep_code", indexes["sigep_code"][val]))

    if "treasury_code" in extended_columns and source.get("treasury_code") is not None:
        val = clean_text(source["treasury_code"])
        if val in indexes["treasury_code"]:
            candidates.append(("treasury_code", indexes["treasury_code"][val]))

    label_key = source["source_key"]
    if label_key in indexes["label"]:
        candidates.append(("label", indexes["label"][label_key]))

    if not candidates:
        return None

    # FIX: Correctly access the row dictionary payload located at index [1] of the candidate tuple
    matched_ids = {str(item[1]["id"]) for item in candidates}
    if len(matched_ids) > 1:
        details = [
            (criterion, row["id"], row["label"]) for criterion, row in candidates
        ]
        raise ValueError(
            f"Los criterios de identificación apuntan a registros distintos: Fuente={source['label']!r}; coincidencias={details}"
        )

    # FIX: Safely return the row dictionary payload mapping asset directly
    return candidates[0][1]


async def persist_actors(
    conn,
    records: list[dict[str, Any]],
    existing: dict[str, dict[str, Any]],
    columns: dict[str, Any],
    extended_columns: set[str],
) -> tuple[int, int, list[dict[str, Any]]]:
    """Performs bulk upsert modifications via ORM statements mapping row values safely."""
    inserted = 0
    updated = 0
    expected: list[dict[str, Any]] = []
    has_updated_at = "updated_at" in columns

    for source in records:
        previous = match_existing_actor(source, existing, extended_columns)
        record_id = str(previous["id"]) if previous else new_uuidv7()

        params: dict[str, Any] = {
            "actor_segment_id": source["actor_segment_id"],
            "label": source["label"],
            "description": source["description"],
            "mission": source["mission"],
            "vision": source["vision"],
            "code": source["code"],
        }

        for col in sorted(extended_columns):
            raw_val = source.get(col)
            if col in {"sigep_code", "treasury_code"}:
                params[col] = cast_to_database_numeric(
                    raw_val, columns[col]["data_type"], column_context=col
                )
            else:
                params[col] = clean_text(raw_val)

        if previous:
            stmt_update = update(Actor).where(Actor.id == record_id).values(**params)
            if has_updated_at:
                stmt_update = stmt_update.values(updated_at=datetime.utcnow())

            await conn.execute(stmt_update)
            updated += 1
        else:
            params["id"] = record_id
            if has_updated_at:
                params["updated_at"] = datetime.utcnow()

            stmt_insert = insert(Actor).values(**params)
            await conn.execute(stmt_insert)
            inserted += 1

        expected.append({"id": record_id, "source_key": source["source_key"], **params})

    return inserted, updated, expected


async def validate_loaded_actors(
    conn, expected: list[dict[str, Any]], extended_columns: set[str]
) -> None:
    """Post-load verification routine cross-checking database state using the ORM model."""
    columns_to_select = [
        Actor.id.label("id"),
        Actor.actor_segment_id.label("actor_segment_id"),
        Actor.label.label("label"),
        Actor.description.label("description"),
        Actor.mission.label("mission"),
        Actor.vision.label("vision"),
        Actor.code.label("code"),
    ]

    for col in sorted(extended_columns):
        if hasattr(Actor, col):
            columns_to_select.append(getattr(Actor, col).label(col))

    stmt = select(*columns_to_select)
    result = await conn.execute(stmt)

    loaded_map: dict[str, dict[str, Any]] = {}
    for r in result.mappings().all():
        row = {
            "id": str(r["id"]),
            "actor_segment_id": str(r["actor_segment_id"]),
            "label": r["label"],
            "description": r["description"],
            "mission": r["mission"],
            "vision": r["vision"],
            "code": r["code"],
        }

        for col in sorted(extended_columns):
            if col in r:
                row[col] = r[col]

        key = fold_for_comparison(row["label"])
        if key:
            if key in loaded_map:
                raise ValueError(
                    f"Entidad duplicada por label normalizado después de cargar: {key}"
                )
            loaded_map[key] = row

    for record in expected:
        key = str(record["source_key"])
        row = loaded_map.get(key)
        if row is None:
            raise ValueError(
                f"No se cargó la entidad esperada en la base de datos: {record['label']}"
            )

        if row["id"] != str(record["id"]):
            raise ValueError(
                f"El UUID cambió inesperadamente para {record['label']!r}."
            )

        fields_to_check = [
            "actor_segment_id",
            "label",
            "description",
            "mission",
            "vision",
            "code",
            *extended_columns,
        ]

        for field in fields_to_check:
            if field in {"sigep_code", "treasury_code"}:
                exp_v = str(record[field]) if record[field] is not None else None
                lod_v = str(row[field]) if row[field] is not None else None
                if exp_v != lod_v:
                    raise ValueError(
                        f"Valor numérico incorrecto en {record['label']!r}.{field}: "
                        f"SQL={row[field]!r}; esperado={record[field]!r}"
                    )
            elif clean_text(row.get(field)) != clean_text(record.get(field)):
                raise ValueError(
                    f"Valor incorrecto para {record['label']!r}.{field}: "
                    f"SQL={row.get(field)!r}; esperado={record.get(field)!r}."
                )


async def upgrade() -> None:
    logger.debug(f"Starting actors population from {ENTITIES_FILE}")

    source_rows = load_normalized_csv(
        ENTITIES_FILE,
        required_columns=SOURCE_REQUIRED_COLUMNS,
        header_aliases=HEADER_ALIASES,
    )
    prepared = validate_and_prepare_source(source_rows)

    sector_count = len({record["sector_key"] for record in prepared})
    print(
        f"[10b] Fuente={ENTITIES_FILE}; entidades={len(prepared)}; "
        f"sectores_referenciados={sector_count}.",
        flush=True,
    )

    async with async_engine.begin() as conn:
        columns = await get_table_columns(conn, schema="actors", table="actors")
        extended_columns = validate_target_columns(columns)

        assert_field_lengths(
            prepared,
            columns,
            fields=[
                "label",
                "description",
                "mission",
                "vision",
                "code",
                *extended_columns,
            ],
        )

        segments = await get_segments_by_key(conn)

        resolved: list[dict[str, Any]] = []
        for src in prepared:
            seg = segments.get(str(src["sector_key"]))
            if seg is None:
                raise ValueError(
                    f"No se encontró el sector en PostgreSQL para la entidad: "
                    f"{src['label']} (Sector: {src['sector']})"
                )
            resolved.append({**src, "actor_segment_id": seg["id"]})

        existing = await get_existing_actors(conn, extended_columns)

        inserted, updated, expected = await persist_actors(
            conn, resolved, existing, columns, extended_columns
        )

        await validate_loaded_actors(conn, expected, extended_columns)

    logger.debug(
        f"actors population finished successfully. "
        f"Inserted={inserted}; updated={updated}; total_source={len(expected)}."
    )
    print(
        f"[10b] OK. Insertados={inserted}; actualizados={updated}; "
        f"entidades_fuente={len(expected)}.",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
