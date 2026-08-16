"""Poblado de forms.forms.

Carga los formularios principales del Índice de Innovación Pública por año:

    IIP 2021
    IIP 2023
    IIP 2025
    IIP 2027

Reglas:
- Cada año es un formulario independiente.
- No se relacionan preguntas entre años.
- Si el formulario no existe, se crea con UUIDv7.
- Si ya existe para ese año, se actualizan label y description.
- Si ya existe pero su ID no es UUIDv7, el script se detiene.
- Los siguientes scripts usarán forms.forms.code para recuperar el form_id.
"""

from uuid import UUID

from sqlalchemy import text
from uuid_utils import uuid7

from shared.infrastructure import async_engine
from shared.utils.logger import get_logger


logger = get_logger(__name__)


FORMS = [
    {
        "code": "2019",
        "label": "Índice de Innovación Pública 2019",
        "description": (
            "Formulario correspondiente a la medición del Índice de Innovación "
            "Pública para la vigencia 2019. Esta estructura se carga como un "
            "instrumento independiente frente a las demás mediciones."
        ),
    },
    {
        "code": "2021",
        "label": "Índice de Innovación Pública 2021",
        "description": (
            "Formulario correspondiente a la medición del Índice de Innovación "
            "Pública para la vigencia 2021. Esta estructura se carga como un "
            "instrumento independiente frente a las demás mediciones."
        ),
    },
    {
        "code": "2023",
        "label": "Índice de Innovación Pública 2023",
        "description": (
            "Formulario correspondiente a la medición del Índice de Innovación "
            "Pública para la vigencia 2023. Esta estructura se carga como un "
            "instrumento independiente frente a las demás mediciones."
        ),
    },
    {
        "code": "2025",
        "label": "Índice de Innovación Pública 2025",
        "description": (
            "Formulario correspondiente a la medición del Índice de Innovación "
            "Pública para la vigencia 2025. Esta estructura se carga como un "
            "instrumento independiente frente a las demás mediciones."
        ),
    },
    {
        "code": "2027",
        "label": "Índice de Innovación Pública 2027",
        "description": (
            "Formulario correspondiente a la medición proyectada del Índice de "
            "Innovación Pública para la vigencia 2027. Esta estructura se carga "
            "como un instrumento independiente frente a las demás mediciones."
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


def clean_text(value):
    """Limpia cadenas vacías."""
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


async def get_table_columns(conn) -> dict:
    """Consulta metadatos reales de forms.forms."""
    query = text(
        """
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'forms'
          AND table_name = 'forms'
        ORDER BY ordinal_position;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    if not rows:
        raise ValueError("No se encontró la tabla forms.forms en PostgreSQL.")

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_required_columns(db_columns: dict) -> None:
    """Valida que la tabla tenga las columnas necesarias."""
    required_columns = {"id", "code", "label", "description"}

    missing = required_columns - set(db_columns.keys())

    if missing:
        raise ValueError(
            "La tabla forms.forms no tiene todas las columnas requeridas. "
            f"Faltan: {sorted(missing)}"
        )


def truncate_if_needed(value, max_length):
    """Recorta texto si la columna tiene límite de longitud."""
    value = clean_text(value)

    if value is None:
        return None

    if max_length is None:
        return value

    if len(value) <= max_length:
        return value

    return value[:max_length]


def prepare_form_record(item: dict, db_columns: dict) -> dict:
    """Prepara un registro para insertar o actualizar."""
    record = {
        "code": item["code"],
        "label": clean_text(item["label"]),
        "description": clean_text(item["description"]),
    }

    if not record["label"]:
        raise ValueError(f"El formulario del año {record['code']} no tiene label.")

    if "label" in db_columns:
        max_length = db_columns["label"]["max_length"]

        if max_length is not None and len(record["label"]) > max_length:
            raise ValueError(
                f"El label del formulario {record['code']} supera "
                f"{max_length} caracteres."
            )

    if "description" in db_columns:
        max_length = db_columns["description"]["max_length"]
        record["description"] = truncate_if_needed(record["description"], max_length)

    if (
        "description" in db_columns
        and not db_columns["description"]["nullable"]
        and record["description"] is None
    ):
        record["description"] = "Sin descripción registrada."

    return record


async def get_existing_form_by_code(conn, code: str):
    """Busca un formulario existente por año."""
    query = text(
        """
        SELECT
            id::text AS id,
            code,
            label,
            description
        FROM forms.forms
        WHERE code = :code;
        """
    )

    result = await conn.execute(query, {"code": code})
    rows = result.mappings().all()

    if len(rows) > 1:
        raise ValueError(
            f"Existe más de un formulario registrado para code={code}. "
            "Debe existir máximo un formulario por año para poder conectar "
            "correctamente secciones y preguntas."
        )

    if not rows:
        return None

    return rows[0]


async def insert_form(conn, record: dict) -> str:
    """Inserta un formulario nuevo con UUIDv7."""
    new_id = new_uuidv7()

    query = text(
        """
        INSERT INTO forms.forms (
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

    await conn.execute(
        query,
        {
            "id": new_id,
            "code": record["code"],
            "label": record["label"],
            "description": record["description"],
        },
    )

    return new_id


async def update_form(conn, existing_id: str, record: dict) -> None:
    """Actualiza label y description de un formulario existente."""
    query = text(
        """
        UPDATE forms.forms
        SET
            label = :label,
            description = :description
        WHERE id = CAST(:id AS uuid);
        """
    )

    await conn.execute(
        query,
        {
            "id": existing_id,
            "label": record["label"],
            "description": record["description"],
        },
    )


async def validate_forms(conn) -> None:
    """Valida que los formularios existan y tengan UUIDv7."""
    expected_years = [item["code"] for item in FORMS]

    query = text(
        """
        SELECT
            id::text AS id,
            code,
            label,
            description
        FROM forms.forms
        WHERE code = ANY(:expected_years)
        ORDER BY code;
        """
    )

    result = await conn.execute(query, {"expected_years": expected_years})
    rows = result.mappings().all()

    found_years = {row["code"] for row in rows}
    expected_years_set = set(expected_years)

    missing = expected_years_set - found_years

    if missing:
        raise ValueError(
            f"No quedaron cargados todos los formularios. "
            f"Faltan años: {sorted(missing)}"
        )

    non_v7 = [
        {
            "code": row["code"],
            "label": row["label"],
            "id": row["id"],
        }
        for row in rows
        if not is_uuidv7(row["id"])
    ]

    if non_v7:
        raise ValueError(
            "Hay formularios con ID que no es UUIDv7. "
            f"Registros problemáticos: {non_v7}"
        )

    duplicated_query = text(
        """
        SELECT
            code,
            COUNT(*) AS total
        FROM forms.forms
        WHERE code = ANY(:expected_years)
        GROUP BY code
        HAVING COUNT(*) > 1;
        """
    )

    duplicated_result = await conn.execute(
        duplicated_query,
        {"expected_years": expected_years},
    )

    duplicated_rows = duplicated_result.mappings().all()

    if duplicated_rows:
        raise ValueError(
            "Hay años duplicados en forms.forms. "
            f"Registros problemáticos: {list(duplicated_rows)}"
        )

    logger.info("forms.forms validation passed successfully.")


async def upgrade() -> None:
    """Carga forms.forms."""
    logger.info("Starting forms.forms population...")

    try:
        async with async_engine.begin() as conn:
            db_columns = await get_table_columns(conn)
            validate_required_columns(db_columns)

            inserted = 0
            updated = 0

            for item in FORMS:
                record = prepare_form_record(item, db_columns)
                code = record["code"]

                existing = await get_existing_form_by_code(conn, code)

                if existing:
                    existing_id = existing["id"]

                    if not is_uuidv7(existing_id):
                        raise ValueError(
                            f"El formulario del año {code} ya existe, pero su ID "
                            f"no es UUIDv7: {existing_id}. "
                            "Como este ID será usado por forms.sections.form_id, "
                            "corrige ese registro antes de continuar."
                        )

                    await update_form(conn, existing_id, record)
                    updated += 1

                    logger.info(
                        f"Updated form code={code} with existing UUIDv7: {existing_id}"
                    )

                else:
                    new_id = await insert_form(conn, record)
                    inserted += 1

                    logger.info(
                        f"Inserted form code={code} with UUIDv7: {new_id}"
                    )

            await validate_forms(conn)

        logger.info(
            f"forms.forms population finished. "
            f"Inserted: {inserted}. Updated: {updated}."
        )

    except Exception as e:
        logger.error(f"Failed to run forms.forms population: {e}")
        raise
