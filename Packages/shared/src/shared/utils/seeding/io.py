import csv
import io
import os
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from shared.utils.seeding.text import clean_text, normalize_key


def read_and_decode_csv(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode CSV file {path}")


def load_normalized_csv(
    path: Path, required_columns: set[str], header_aliases: dict[str, str]
) -> list[dict[str, Any]]:
    """Loads any seeding CSV file, normalizes header structures, and applies column aliases."""
    csv_text = read_and_decode_csv(path)

    try:
        delimiter = csv.Sniffer().sniff(csv_text[:20000], delimiters=";,|\t").delimiter
    except csv.Error:
        delimiter = ";"

    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
    if reader.fieldnames is None:
        raise ValueError(f"CSV {path} does not contain headers.")

    normalized_headers = []
    for name in reader.fieldnames:
        norm = normalize_key(name) or ""
        norm = norm.replace(" ", "_")
        normalized_headers.append(header_aliases.get(norm, norm))

    missing = required_columns - set(normalized_headers)
    if missing:
        raise ValueError(
            f"Missing mandatory columns in CSV {path.name}: {sorted(missing)}"
        )

    rows = []
    for idx, raw_row in enumerate(reader, start=2):
        row: dict[str, Any] = {
            normalized_headers[i]: clean_text(raw_row.get(orig))
            for i, orig in enumerate(reader.fieldnames)
        }
        row["_line_number"] = idx
        if not all(v is None for k, v in row.items() if k != "_line_number"):
            rows.append(row)

    return rows


def load_clean_excel_sheet(
    excel_file: pd.ExcelFile,
    sheet_name: str,
    required_columns: set[str],
    ffill_columns: Sequence[str] | None = None,  # Upgraded type flexibility
) -> pd.DataFrame:
    """Loads a specific sheet, forces type object, strips columns, forward-fills hierarchies, and cleans strings."""
    if sheet_name not in excel_file.sheet_names:
        raise ValueError(f"Sheet '{sheet_name}' is missing.")

    df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=object)
    df.columns = [str(col).strip() for col in df.columns]

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Sheet '{sheet_name}' is missing columns: {sorted(missing)}")

    for col in df.columns:
        df[col] = df[col].apply(clean_text)

    if ffill_columns:
        # Cast to list internally to fulfill pandas indexing demands safely
        df[list(ffill_columns)] = df[list(ffill_columns)].ffill()

    return df



def get_seeding_active_years(default_years: Sequence[int] = (2019, 2021, 2023, 2025)) -> tuple[int, ...]:
    """Retrieves target operational years from environment scopes with runtime safety checks."""
    raw_value = os.getenv("IIP_ACTIVE_YEARS")
    if not raw_value:
        return tuple(default_years)

    years: list[int] = []
    for value in raw_value.split(","):
        stripped = value.strip()
        if not stripped:
            continue
        try:
            years.append(int(stripped))
        except ValueError as exc:
            raise ValueError(
                f"IIP_ACTIVE_YEARS must contain comma-separated integers. Invalid: {value!r}"
            ) from exc

    if not years:
        raise ValueError("IIP_ACTIVE_YEARS environment variable evaluates to an empty configuration.")
    if len(years) != len(set(years)):
        raise ValueError(f"IIP_ACTIVE_YEARS contains duplicate entries: {years}")

    return tuple(years)
