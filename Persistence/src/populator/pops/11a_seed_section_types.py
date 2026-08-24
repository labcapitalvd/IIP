"""Poblado de forms.section_types utilizando Modelos ORM.

Carga y mantiene sincronizados los tipos de sección necesarios para estructurar
el IIP utilizando los modelos declarativos del sistema y las utilidades compartidas.
"""

from __future__ import annotations

import asyncio
from typing import Any

from shared.infrastructure import async_engine
from shared.models import SectionType
from shared.utils.logger import get_logger
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_field_lengths,
    assert_no_duplicates,
    assert_no_missing,
    clean_text,
    get_table_columns,
    is_uuidv7,
    new_uuidv7,
    validate_required_columns,
)
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

logger = get_logger(__name__)

# Schema metadata descriptors for schema boundary checks
SCHEMA_NAME = "forms"
TABLE_NAME = "section_types"
REQUIRED_COLUMNS = {"id", "code", "label", "description"}

# Configuration dataset bound directly to system operational targets
SECTION_TYPES_DATA = [
    {
        "code": "C",
        "label": "COMPONENTE",
        "description": clean_text(
            "Nivel principal de organización del formulario. Agrupa un conjunto "
            "amplio de variables, indicadores y preguntas asociadas a una "
            "dimensión temática del instrumento."
        ),
    },
    {
        "code": "V",
        "label": "VARIABLE",
        "description": clean_text(
            "Nivel intermedio de organización del formulario. Representa una "
            "dimensión específica dentro de un componente y permite agrupar "
            "indicadores o preguntas relacionadas."
        ),
    },
    {
        "code": "I",
        "label": "INDICADOR",
        "description": clean_text(
            "Nivel específico de medición dentro del formulario. Representa el "
            "elemento concreto que se quiere observar, evaluar o medir mediante "
            "una o varias preguntas."
        ),
    },
]


async def get_existing_section_type(
    conn: AsyncConnection, label: str
) -> dict[str, Any] | None:
    """Busca un tipo de sección existente por su etiqueta utilizando mapeos dict."""
    stmt = select(SectionType.id.label("id")).where(SectionType.label == label).limit(1)
    result = await conn.execute(stmt)
    row = result.mappings().first()
    return dict(row) if row else None


async def insert_section_type(conn: AsyncConnection, record: dict) -> None:
    """Inserta un nuevo registro utilizando la estructura del modelo ORM."""
    # This compiles into a clean insert statement bound to your ORM model's schema mapping
    stmt = insert(SectionType).values(
        id=record["id"],
        code=record["code"],
        label=record["label"],
        description=record["description"],
    )
    await conn.execute(stmt)


async def update_section_type_description(conn: AsyncConnection, record: dict) -> None:
    """Actualiza la descripción de un tipo de sección existente de forma explícita."""
    stmt = (
        update(SectionType)
        .where(SectionType.label == record["label"])
        .values(description=record["description"], code=record["code"])
    )
    await conn.execute(stmt)


async def validate_database_integrity(conn: AsyncConnection) -> None:
    """Realiza validaciones rigurosas post-carga usando las utilidades compartidas."""
    expected_labels = {item["label"] for item in SECTION_TYPES_DATA}

    # FIX: Explicitly select the individual column attributes needed for the dictionary mapping
    stmt = select(
        SectionType.id.label("id"),
        SectionType.code.label("code"),
        SectionType.label.label("label"),
        SectionType.description.label("description"),
    ).where(SectionType.label.in_(expected_labels))

    result = await conn.execute(stmt)

    # FIX: Use .mappings().all() to handle AsyncConnection row payloads safely (exactly like seed entities)
    rows = [
        {
            "id": str(row["id"]),
            "code": row["code"],
            "label": row["label"],
            "description": row["description"],
        }
        for row in result.mappings().all()
    ]

    # 1. Verificar duplicados locales devueltos por la base de datos
    assert_no_duplicates(
        rows, key_fields=["label"], what="tipos de sección por etiqueta"
    )
    assert_no_duplicates(rows, key_fields=["code"], what="tipos de sección por código")

    # 2. Verificar que todo lo esperado se encuentre cargado exitosamente
    labels_found = {row["label"] for row in rows}
    assert_no_missing(expected_labels, labels_found, what="tipos de sección (labels)")

    # 3. Validar la estructura e integridad de claves primarias UUIDv7
    assert_all_uuidv7(rows, id_key="id", label_key="label")

    logger.debug("section_types structural post-load integrity validation passed.")


async def upgrade() -> None:
    """Ejecuta el ciclo de vida de poblado utilizando los modelos ORM del sistema."""
    logger.info(
        f"Starting database population via ORM for {SCHEMA_NAME}.{TABLE_NAME}..."
    )

    try:
        async with async_engine.begin() as conn:
            # Fase de Introspección: Validar esquema real de la BD antes de transaccionar
            columns_meta = await get_table_columns(
                conn, schema=SCHEMA_NAME, table=TABLE_NAME
            )
            validate_required_columns(
                columns_meta, REQUIRED_COLUMNS, f"{SCHEMA_NAME}.{TABLE_NAME}"
            )

            # Verificar límites de longitud de caracteres provistos
            assert_field_lengths(SECTION_TYPES_DATA, columns_meta, ["code", "label"])

            # Validar que los datos estáticos locales no tengan duplicados accidentales
            assert_no_duplicates(
                SECTION_TYPES_DATA, key_fields=["code"], what="Configuración de códigos"
            )
            assert_no_duplicates(
                SECTION_TYPES_DATA,
                key_fields=["label"],
                what="Configuración de etiquetas",
            )

            inserted = 0
            updated = 0

            for item in SECTION_TYPES_DATA:
                label = item["label"]
                code = item["code"]
                description = item["description"]

                # OPTIMIZED: Guarantees BOTH label and code types to the linter safely
                if not isinstance(label, str) or not isinstance(code, str):
                    continue

                existing = await get_existing_section_type(conn, label)

                if existing:
                    existing_id = str(existing["id"])

                    # Lanzar error si la llave actual viola la directiva UUIDv7
                    if not is_uuidv7(existing_id):
                        raise ValueError(
                            f"Inconsistencia crítica detectada por ORM: El registro '{label}' "
                            f"tiene un identificador primario no compatible con UUIDv7: {existing_id}. "
                            f"Por favor corrija este registro manualmente antes de reintentar."
                        )

                    await update_section_type_description(
                        conn,
                        {
                            "code": code,
                            "label": label,
                            "description": description,
                        },
                    )
                    updated += 1
                    logger.debug(
                        f"Updated record '{label}' using matching UUIDv7: {existing_id}"
                    )
                else:
                    new_id = new_uuidv7()
                    await insert_section_type(
                        conn,
                        {
                            "id": new_id,
                            "code": code,
                            "label": label,
                            "description": description,
                        },
                    )
                    inserted += 1

            # Validaciones de cierre y consistencia estructural
            await validate_database_integrity(conn)

        logger.info(
            f"Successfully processed seed updates via ORM for {SCHEMA_NAME}.{TABLE_NAME}. "
            f"Inserted: {inserted}, Updated: {updated}."
        )

    except Exception as e:
        logger.error(
            f"Seeding lifecycle failed for model table {SCHEMA_NAME}.{TABLE_NAME}: {e}"
        )
        raise


if __name__ == "__main__":
    asyncio.run(upgrade())
