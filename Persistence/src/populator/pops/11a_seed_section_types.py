"""Poblado de forms.section_types.

Carga los tipos de sección necesarios para estructurar el IIP:

    COMPONENTE
    VARIABLE
    INDICADOR

Estos IDs serán usados después por forms.sections.section_type_id.

Regla técnica:
- Si el tipo de sección no existe, se crea con UUIDv7.
- Si ya existe, se actualiza la descripción y se conserva su ID.
- Si ya existe pero su ID no es UUIDv7, el script se detiene para evitar
  inconsistencias silenciosas.
"""

from uuid import UUID

from shared.infrastructure import async_engine
from shared.utils.logger import get_logger
from sqlalchemy import text
from uuid_utils import uuid7

logger = get_logger(__name__)


SECTION_TYPES = [
    {
        "code": "C",
        "label": "COMPONENTE",
        "description": (
            "Nivel principal de organización del formulario. Agrupa un conjunto "
            "amplio de variables, indicadores y preguntas asociadas a una "
            "dimensión temática del instrumento."
        ),
    },
    {
        "code": "V",
        "label": "VARIABLE",
        "description": (
            "Nivel intermedio de organización del formulario. Representa una "
            "dimensión específica dentro de un componente y permite agrupar "
            "indicadores o preguntas relacionadas."
        ),
    },
    {
        "code": "I",
        "label": "INDICADOR",
        "description": (
            "Nivel específico de medición dentro del formulario. Representa el "
            "elemento concreto que se quiere observar, evaluar o medir mediante "
            "una o varias preguntas."
        ),
    },
]


def new_uuidv7() -> str:
    """Genera UUID versión 7 usando la misma librería del proyecto."""
    return str(uuid7())


def is_uuidv7(value) -> bool:
    """Valida que un ID sea UUID versión 7."""
    if value is None:
        return False

    try:
        parsed = UUID(str(value))
        return parsed.version == 7
    except Exception:
        return False


async def get_existing_section_type(conn, label: str):
    """Busca un tipo de sección existente por label."""
    query = text(
        """
        SELECT
            id::text AS id,
            code,
            label,
            description
        FROM forms.section_types
        WHERE label = :label
        LIMIT 1;
        """
    )

    result = await conn.execute(query, {"label": label})
    return result.mappings().first()


async def insert_section_type(conn, record: dict) -> None:
    """Inserta un nuevo tipo de sección con UUIDv7."""
    query = text(
        """
        INSERT INTO forms.section_types (
            id,
            code,
            label,
            description
        )
        VALUES (
            CAST(:id AS uuid),
            :code,
            :label,
            :description
        );
        """
    )

    await conn.execute(query, record)


async def update_section_type_description(conn, record: dict) -> None:
    """Actualiza la descripción de un tipo de sección existente."""
    query = text(
        """
        UPDATE forms.section_types
        SET description = :description
        WHERE label = :label;
        """
    )

    await conn.execute(
        query,
        {
            "label": record["label"],
            "description": record["description"],
        },
    )


async def validate_section_types(conn) -> None:
    """Valida que los tres tipos existan y que todos tengan UUIDv7."""
    query = text(
        """
        SELECT
            id::text AS id,
            label,
            description
        FROM forms.section_types
        WHERE label IN ('COMPONENTE', 'VARIABLE', 'INDICADOR')
        ORDER BY label;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    labels_found = {row["label"] for row in rows}
    labels_expected = {item["label"] for item in SECTION_TYPES}

    missing = labels_expected - labels_found

    if missing:
        raise ValueError(
            f"No quedaron cargados todos los tipos de sección. Faltan: {sorted(missing)}"
        )

    non_v7 = [
        {"label": row["label"], "id": row["id"]}
        for row in rows
        if not is_uuidv7(row["id"])
    ]

    if non_v7:
        raise ValueError(
            "Hay tipos de sección con ID que no es UUIDv7. "
            f"Registros problemáticos: {non_v7}"
        )

    logger.debug("section_types validation passed successfully.")


async def upgrade() -> None:
    """Carga forms.section_types."""
    logger.debug("Starting forms.section_types population...")

    try:
        async with async_engine.begin() as conn:
            inserted = 0
            updated = 0

            for item in SECTION_TYPES:
                code = item["code"]
                label = item["label"]
                description = item["description"]

                existing = await get_existing_section_type(conn, label)

                if existing:
                    existing_id = existing["id"]

                    if not is_uuidv7(existing_id):
                        raise ValueError(
                            f"El tipo de sección '{label}' ya existe, pero su ID "
                            f"no es UUIDv7: {existing_id}. "
                            "Como esta tabla será referenciada por forms.sections, "
                            "corrige este ID antes de continuar o reinicia esta tabla "
                            "si todavía no tiene dependencias."
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
                        f"Updated section_type '{label}' with existing UUIDv7: {existing_id}"
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
                    logger.debug(f"Inserted section_type '{label}' with UUIDv7: {new_id}")

            await validate_section_types(conn)

        logger.debug(
            f"forms.section_types population finished. "
            f"Inserted: {inserted}. Updated: {updated}."
        )

    except Exception as e:
        logger.error(f"Failed to run forms.section_types population: {e}")
        raise
