"""Utilidades de validación post-carga para scripts de poblado (seed).

Reemplaza el patrón repetido en cada `validate_*()` de los scripts de
`pops/`: comparar claves esperadas vs. encontradas, verificar que todos
los IDs sean UUIDv7 y detectar duplicados.

Utiliza las herramientas visuales globales del sistema para formatear listas
de fallas con alta legibilidad en la consola de terminal.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Set as AbstractSet
from typing import Any, Hashable, Sequence

from shared.utils.texts import format_list

from .ids import is_uuidv7


def assert_no_missing(
    expected: AbstractSet[Hashable], found: AbstractSet[Hashable], *, what: str
) -> None:
    """Verifica que todo lo esperado haya quedado cargado.

    `what` describe la entidad para el mensaje de error, p.ej.
    "tipos de sección" o "formularios (años)". En caso de fallo, renderiza
    una cuadrícula alineada de los elementos faltantes.
    """
    missing = expected - found
    if missing:
        error_grid = format_list(
            title=f"Faltan {what} por cargar",
            items=[str(item) for item in missing],
            cols=2,
            sort=True,
        )
        raise ValueError(f"Validación de Integridad Fallida:{error_grid}")


def assert_all_uuidv7(
    rows: Sequence[dict[str, Any]], *, id_key: str = "id", label_key: str | None = None
) -> None:
    """Verifica que todas las filas tengan un ID UUIDv7 válido.

    `label_key`, si se provee, se incluye en el mensaje de error para
    identificar más fácil el registro problemático (p.ej. "code" o
    "label"). Muestra los problemas en un formato de lista en bloque limpio.
    """
    bad_rows = [row for row in rows if not is_uuidv7(row.get(id_key))]
    if bad_rows:
        if label_key:
            details = [
                f"{row.get(label_key)} -> ({id_key}: {row.get(id_key)})"
                for row in bad_rows
            ]
        else:
            details = [f"({id_key}: {row.get(id_key)})" for row in bad_rows]

        error_grid = format_list(
            title=f"Registros con identificador inválido ({id_key})",
            items=details,
            cols=1,
            sort=False,
        )
        raise ValueError(f"Error de llave primaria:{error_grid}")


def assert_no_duplicates(
    rows: Sequence[dict[str, Any]], *, key_fields: Sequence[str], what: str
) -> None:
    """Verifica que no existan filas duplicadas según `key_fields`.

    Útil para detectar, por ejemplo, más de un formulario para el mismo
    `code`, o más de un field_choice para el mismo (field_id, display_order).
    """
    keys = [tuple(row.get(field) for field in key_fields) for row in rows]
    counts = Counter(keys)
    duplicated = [key for key, count in counts.items() if count > 1]

    if duplicated:
        details = [str(key) for key in duplicated]
        error_grid = format_list(
            title=f"Claves duplicadas encontradas para {what}",
            items=details,
            cols=1,
            sort=True,
        )
        raise ValueError(f"Hay {what} duplicados según {list(key_fields)}:{error_grid}")
