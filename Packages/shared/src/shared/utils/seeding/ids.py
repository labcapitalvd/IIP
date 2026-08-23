"""Utilidades de identificadores para scripts de poblado (seed).

Reemplaza las implementaciones duplicadas de `is_uuidv7` / `new_uuidv7`
presentes en los scripts de la carpeta `pops/`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from uuid_utils import uuid7

__all__ = ["new_uuidv7", "is_uuidv7"]


def new_uuidv7() -> str:
    """Genera un nuevo UUID versión 7 en formato string."""
    return str(uuid7())


def is_uuidv7(value: Any) -> bool:
    """Valida que `value` sea un UUID versión 7.

    Acepta str, UUID o cualquier valor convertible a str. Devuelve False
    (en vez de lanzar excepciones) para None, cadenas vacías o valores malformados,
    de modo que pueda usarse directamente en condicionales de validación.
    """
    if value is None:
        return False

    value = str(value).strip()
    if not value:
        return False

    try:
        return UUID(value).version == 7
    except (ValueError, TypeError, AttributeError):
        return False
