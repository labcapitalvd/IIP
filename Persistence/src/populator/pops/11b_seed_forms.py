"""Poblado de forms.forms.

Carga los formularios principales del Índice de Innovación Pública por año:
    IIP 2019, 2021, 2023, 2025, 2027

Reglas:
- Cada año es un formulario independiente.
- Si el formulario no existe, se crea con un nuevo UUIDv7.
- Si ya existe para ese año, se actualizan sus atributos (label y description).
- Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
"""

# Infraestructura y Modelos globales del proyecto
from shared.infrastructure import async_engine

# Importación del Modelo ORM centralizado
from shared.models import (
    Form,
)
from shared.utils.logger import get_logger

# Utilidades globales de Seeding compartidas
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_no_duplicates,
    assert_no_missing,
    clean_text,
    get_table_columns,
    new_uuidv7,
    truncate_text,
    validate_required_columns,
)
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

logger = get_logger(__name__)

# Definición de datos maestros estructurados
FORMS_DATA = [
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


def prepare_form_record(item: dict, db_columns: dict) -> dict:
    """Aplica limpieza de texto, validaciones de nulidad y recortes según el esquema."""
    record = {
        "code": item["code"],
        "label": clean_text(item["label"]),
        "description": clean_text(item["description"]),
    }

    if not record["label"]:
        raise ValueError(
            f"El formulario del año {record['code']} no tiene un label válido."
        )

    # Validar y recortar el campo label usando metadatos dinámicos
    if "label" in db_columns:
        max_len = db_columns["label"]["max_length"]
        if max_len is not None and len(record["label"]) > int(max_len):
            raise ValueError(
                f"El label del formulario {record['code']} supera el límite de {max_len} caracteres."
            )

    # Validar y recortar el campo description
    if "description" in db_columns:
        max_len = db_columns["description"]["max_length"]
        record["description"] = truncate_text(record["description"], max_len)

        # Manejo de nulidad si la columna de la BD es requerida
        if not db_columns["description"]["nullable"] and record["description"] is None:
            record["description"] = "Sin descripción registrada."

    return record


async def validate_forms_state(
    conn: AsyncConnection, expected_codes: list[str]
) -> None:
    """Ejecuta un set estricto de aserciones de integridad post-carga usando las utilidades."""
    # Consultar el estado final de las filas cargadas utilizando el modelo ORM
    stmt = select(Form.id, Form.code, Form.label).where(Form.code.in_(expected_codes))
    result = await conn.execute(stmt)
    rows = [dict(row) for row in result.mappings().all()]

    # 1. Verificar que no falte ningún formulario esperado en el destino
    found_codes = {row["code"] for row in rows}
    assert_no_missing(
        expected=set(expected_codes), found=found_codes, what="formularios (años)"
    )

    # 2. Verificar la validez de los identificadores UUIDv7 primarios
    assert_all_uuidv7(rows=rows, id_key="id", label_key="code")

    # 3. Detectar si existen claves duplicadas a nivel de BD para este ámbito
    assert_no_duplicates(rows=rows, key_fields=["code"], what="formularios de medición")

    logger.debug("Validaciones de integridad para forms.forms completadas con éxito.")


# ... rest of your setup ...


async def upgrade() -> None:
    """Punto de entrada principal para ejecutar el poblado idempotente de formularios."""
    logger.debug("Iniciando el proceso de poblado para forms.forms...")

    try:
        async with async_engine.begin() as conn:
            # Consultar y validar metadatos reales del esquema de la tabla de destino
            db_columns = await get_table_columns(conn, schema="forms", table="forms")
            validate_required_columns(
                db_columns,
                required={"id", "code", "label", "description"},
                table_name="forms.forms",
            )

            inserted = 0
            updated = 0
            expected_codes = [item["code"] for item in FORMS_DATA]

            for item in FORMS_DATA:
                record = prepare_form_record(item, db_columns)
                code = record["code"]

                # Buscar registros existentes por su código único de negocio utilizando el modelo ORM
                stmt_select = select(Form.id).where(Form.code == code)
                existing_row = (await conn.execute(stmt_select)).mappings().first()

                if existing_row:
                    existing_id = str(existing_row["id"])

                    # Ejecutar actualización sobre el registro mapeado por el ORM
                    stmt_update = (
                        update(Form)
                        .where(Form.id == existing_row["id"])
                        .values(
                            label=record["label"], description=record["description"]
                        )
                    )
                    await conn.execute(stmt_update)
                    updated += 1
                    logger.debug(
                        f"Formulario actualizado: code={code} | ID={existing_id}"
                    )
                else:
                    # Generar un ID UUIDv7 nativo compatible y realizar la inserción segura
                    new_id = new_uuidv7()

                    # Core insert helper used cleanly with the declarative model
                    stmt_insert = insert(Form).values(
                        id=new_id,
                        code=record["code"],
                        label=record["label"],
                        description=record["description"],
                    )
                    await conn.execute(stmt_insert)
                    inserted += 1

            # Ejecutar el motor centralizado de validaciones post-carga
            await validate_forms_state(conn, expected_codes)

        logger.info(
            f"Poblado de forms.forms finalizado con éxito. Creados: {inserted}. Actualizados: {updated}."
        )

    except Exception as e:
        logger.error(f"Fallo crítico al ejecutar el poblado de forms.forms: {e}")
        raise
