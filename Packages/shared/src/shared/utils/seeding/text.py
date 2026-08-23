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
