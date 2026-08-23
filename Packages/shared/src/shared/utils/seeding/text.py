"""Utilidades de texto para scripts de poblado (seed).

Reemplaza las implementaciones duplicadas de `clean_text` / `clean`,
`normalize_key` / `normalize_text` y `truncate_text` / `truncate`
presentes en los scripts de la carpeta `pops/`.

Mantiene las transformaciones NFKD desacopladas de las configuraciones de
producción en vivo (NFKC) para asegurar estabilidad en operaciones de matching.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import pandas as pd

__all__ = [
    "clean_text",
    "fold_for_comparison",
    "generate_technical_slug",
    "truncate_text",
]


def clean_text(value: Any) -> Optional[str]:
    """Limpia un valor proveniente de Excel o de la BD.

    - Colapsa NaN/None/pd.NA a None.
    - Recorta espacios.
    - Colapsa cadenas vacías (tras el strip) a None.

    Es seguro pasarle cualquier tipo de valor (str, número, Timestamp,
    NaN de pandas, etc.).
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        # pd.isna falla para algunos tipos (p.ej. listas); si no es NaN,
        # simplemente continuamos con la conversión a texto.
        pass

    value = str(value).strip()
    return value or None


def remove_diacritics(value: str) -> str:
    """Remueve de manera atómica acentos y marcas diacríticas usando NFKD."""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def fold_for_comparison(value: Any) -> Optional[str]:
    """Normaliza texto para comparaciones insensibles a acentos/mayúsculas.

    Aplica clean_text, remueve diacríticos (NFKD), pasa a minúsculas
    (casefold) y colapsa espacios múltiples. Útil para comparar labels
    o hacer lookups por nombre entre Excel y BD.
    """
    value = clean_text(value)
    if value is None:
        return None

    no_accents = remove_diacritics(value)
    lowercased = no_accents.casefold()
    return re.sub(r"\s+", " ", lowercased).strip()


def generate_technical_slug(value: Any) -> Optional[str]:
    """Genera identificadores técnicos en formato snake_case estricto.

    Toma un valor de texto crudo, aplica el plegamiento de diacríticos, elimina
    símbolos de puntuación especiales y convierte los espacios en guiones bajos.
    Ideal para rellenar campos de códigos dinámicos en la base de datos (p.ej., 'code').
    """
    folded = fold_for_comparison(value)
    if folded is None:
        return None

    stripped = re.sub(r"[^a-z0-9\s]+", "", folded)
    return re.sub(r"\s+", "_", stripped).strip("_")


def truncate_text(value: Any, max_length: Optional[int]) -> Optional[str]:
    """Limpia y recorta `value` a `max_length` caracteres.

    Si max_length es None (columna sin límite), el valor no se recorta.
    """
    value = clean_text(value)
    if value is None or max_length is None:
        return value
    return value[:max_length]


def normalize_key(value: Any) -> Optional[str]:
    """Centralized, robust text normalizer for database crosses and idempotency hashes."""
    if value is None:
        return None
    # Assuming clean_text handles basic string formatting / stripping
    from shared.utils.seeding import clean_text

    cleaned = clean_text(value)
    if cleaned is None:
        return None

    # Strip diacritics / accents
    normalized = unicodedata.normalize("NFKD", cleaned)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))

    # Standardize casing and substitute whitespace/special chars
    normalized = normalized.casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or None


def extract_numeric_suffix(value: Any) -> Optional[str]:
    """Extracts numeric hierarchies cleanly (e.g., 'Pregunta 28.1' -> '28_1')."""
    from shared.utils.seeding import clean_text

    cleaned = clean_text(value)
    if not cleaned:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)*)", cleaned)
    if not match:
        return None
    return match.group(1).replace(".", "_").replace(",", "_")


def compute_hierarchical_order(value: Any) -> int:
    """Computes a stable integer coordinate for sorting multi-tiered hierarchies.

    Examples:
        'Pregunta 1'     -> 1000
        'Variable 2.1'   -> 2001
        'Indicador 3.2.1' -> 3002001
    """
    cleaned = clean_text(value)
    if cleaned is None:
        return 0

    match = re.search(r"(\d+(?:[.,]\d+)*)", cleaned)
    if not match:
        return 0

    normalized = match.group(1).replace(",", ".")
    parts = [int(part) for part in normalized.split(".") if part.isdigit()]

    if not parts:
        return 0
    if len(parts) == 1:
        return parts[0] * 1000

    order = parts[0] * 1000 + parts[1]
    for part in parts[2:]:
        order = order * 1000 + part
    return order


def cast_to_database_numeric(
    value: Any, udt_type_name: str, column_context: str
) -> str | int | Decimal | None:
    """Coerces raw metadata strings into type-safe Python/SQL primitive fields."""
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    target_type = str(udt_type_name).lower()
    if target_type in {"smallint", "integer", "bigint", "int2", "int4", "int8"}:
        try:
            return int(cleaned)
        except ValueError as exc:
            raise ValueError(
                f"{column_context}={value!r} cannot be converted to integer."
            ) from exc

    if target_type in {
        "numeric",
        "decimal",
        "real",
        "float4",
        "float8",
        "double precision",
    }:
        try:
            return Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(
                f"{column_context}={value!r} cannot be converted to Decimal."
            ) from exc

    return cleaned
