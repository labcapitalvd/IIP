"""Poblado de actor_segments desde carpeta local jhonatan.

Por defecto lee:
    /api/populator/pops/jhonatan/actors.actor_segments_template.csv

La llamada a GitHub queda disponible, pero apagada por defecto.
Para usar GitHub en el futuro:
    POPULATOR_SOURCE=github
"""

import os
from io import StringIO
from pathlib import Path
from uuid import UUID

import pandas as pd
from uuid_utils import uuid7

from shared_utils.logger import get_logger
from shared_schemas import ActorSegmentSchema


logger = get_logger("pop/actor_segments")


ORIGIN_URL = (
    "https://api.github.com/repos/LABCapital-VD/IIP-Cuadernos-Jupyter/contents/"
    "Gestión/Migración a DB/output/actors.actor_segments_template.csv"
)

LOCAL_FILE = os.getenv(
    "ACTOR_SEGMENTS_FILE",
    "/api/populator/pops/jhonatan/actors.actor_segments_template.csv",
)

SOURCE = os.getenv("POPULATOR_SOURCE", "local").lower()


def clean_text(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def is_uuidv7(value) -> bool:
    if value is None or str(value).strip() == "":
        return False

    try:
        return UUID(str(value).strip()).version == 7
    except Exception:
        return False


def normalize_uuidv7(value) -> str:
    if is_uuidv7(value):
        return str(UUID(str(value).strip()))

    return str(uuid7())


def read_csv_auto(path_or_text: str, from_text: bool = False) -> pd.DataFrame:
    if from_text:
        return pd.read_csv(
            StringIO(path_or_text),
            sep=None,
            engine="python",
            dtype=str,
        )

    path = Path(path_or_text)

    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo local: {path}")

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(
                path,
                sep=None,
                engine="python",
                dtype=str,
                encoding=encoding,
            )
        except UnicodeDecodeError:
            continue

    raise ValueError(f"No fue posible leer el archivo: {path}")


async def load_dataframe(gh) -> pd.DataFrame:
    if SOURCE == "github":
        logger.info("Loading actor_segments from GitHub...")
        csv_text = await gh.get_raw_text(ORIGIN_URL)
        return read_csv_auto(csv_text, from_text=True)

    logger.info(f"Loading actor_segments from local file: {LOCAL_FILE}")
    return read_csv_auto(LOCAL_FILE, from_text=False)


def prepare_actor_segments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    required_columns = {"label", "description", "id"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Faltan columnas obligatorias en actor_segments: {sorted(missing_columns)}"
        )

    df = df[["label", "description", "id"]]
    df = df.dropna(how="all")

    for col in ["label", "description", "id"]:
        df[col] = df[col].apply(clean_text)

    df = df[df["label"].notna()].copy()

    if df.empty:
        return df

    duplicated_labels = df[df["label"].duplicated(keep=False)]["label"].tolist()
    if duplicated_labels:
        raise ValueError(
            f"Hay sectores duplicados por label: {sorted(set(duplicated_labels))}"
        )

    df["description"] = df["description"].fillna("Sin descripción registrada.")

    too_long_labels = df[df["label"].str.len() > 255]["label"].tolist()
    if too_long_labels:
        raise ValueError(
            f"Hay labels de sectores con más de 255 caracteres: {too_long_labels}"
        )

    df["id"] = df["id"].apply(normalize_uuidv7)

    return df


async def upgrade(gh, api) -> None:
    logger.info("Starting actor_segments population...")

    try:
        df_raw = await load_dataframe(gh)
        df = prepare_actor_segments(df_raw)

        if df.empty:
            logger.info("actor_segments file is empty after cleaning.")
            return

        try:
            existing_entries = await api.get_entries("/actor_segments/all")
            existing_labels = {
                str(entry.get("label")).strip()
                for entry in existing_entries
                if entry.get("label")
            }
        except Exception as e:
            logger.warning(
                "Could not fetch existing actor_segments, assuming empty table. "
                f"Error: {e}"
            )
            existing_labels = set()

        df_to_insert = df[~df["label"].isin(existing_labels)].copy()

        if df_to_insert.empty:
            logger.info("No new rows to insert for /actor_segments/new.")
            return

        records_to_send = (
            df_to_insert
            .where(pd.notna(df_to_insert), None)
            .to_dict(orient="records")
        )

        await api.create_multiple_entries(
            endpoint="/actor_segments/new",
            schema=ActorSegmentSchema,
            data_list=records_to_send,
        )

        logger.info(
            f"actor_segments population finished: {len(records_to_send)} rows sent."
        )

    except Exception as e:
        logger.error(f"Failed to run actor_segments upgrade: {e}")
        raise