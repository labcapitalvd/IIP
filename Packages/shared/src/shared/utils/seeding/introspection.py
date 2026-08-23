"""Utilidades de introspección de esquema para scripts de poblado (seed).

Reemplaza las implementaciones duplicadas de `get_table_columns` /
`table_columns` presentes en los scripts de la carpeta `pops/`.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

ColumnMeta = dict[str, Any]


async def get_table_columns(
    conn: AsyncConnection, schema: str, table: str
) -> dict[str, ColumnMeta]:
    """Consulta los metadatos reales de una tabla vía information_schema.

    Retorna un dict {column_name: {"data_type", "max_length", "nullable"}}.
    Lanza ValueError si la tabla no existe (0 columnas encontradas), lo
    cual también cubre errores de nombre de schema/tabla mal escritos.
    """
    result = await conn.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
            ORDER BY ordinal_position;
            """
        ),
        {"schema": schema, "table": table},
    )
    rows = result.mappings().all()

    if not rows:
        raise ValueError(f"No se encontró la tabla {schema}.{table} en PostgreSQL.")

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


def validate_required_columns(
    columns: Mapping[str, ColumnMeta], required: set[str], table_name: str
) -> None:
    """Valida que `columns` tenga todas las llaves obligatorias configuradas.

    Lanza ValueError con el nombre de la tabla y las columnas faltantes.
    """
    missing = required - set(columns.keys())
    if missing:
        raise ValueError(
            f"La tabla {table_name} no tiene todas las columnas requeridas. "
            f"Faltan: {sorted(missing)}"
        )


def assert_field_lengths(
    records: Sequence[Mapping[str, Any]],
    columns: Mapping[str, ColumnMeta],
    fields: Sequence[str],
) -> None:
    """Centralized boundary engine checking string fields lengths against database limits.

    Raises ValueError with a formatted preview sample grid if boundaries are crossed.
    """
    for field in fields:
        if field not in columns:
            continue

        max_len = columns[field]["max_length"]
        if max_len is None:
            continue

        max_len_int = int(max_len)
        too_long = [
            str(record[field])
            for record in records
            if record.get(field) is not None and len(str(record[field])) > max_len_int
        ]

        if too_long:
            raise ValueError(
                f"Hay valores de '{field}' que superan el límite de "
                f"{max_len_int} caracteres en el esquema: {too_long[:10]}"
            )
