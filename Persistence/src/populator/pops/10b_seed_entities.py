"""Poblado de actors desde carpeta local jhonatan.

Lee:
    /api/populator/pops/jhonatan/actors.actors_template.csv

y:
    /api/populator/pops/jhonatan/actors.actor_segments_template.csv

Este script NO usa el endpoint /actors/new para insertar entidades.
Hace UPSERT directo sobre PostgreSQL porque:
1. El endpoint no tiene método update.
2. Si la entidad ya existe por label, no se actualizan campos faltantes.
3. Algunos campos nuevos como sigep_code, treasury_code e initials pueden no pasar
   correctamente por el schema de la API si no está actualizado.

La relación actor_segment_id se resuelve así:
    actor_segment_id del CSV de entidades
        -> label del sector en actors.actor_segments_template.csv
        -> id real del sector en PostgreSQL
"""

import os
import re
import unicodedata
from io import StringIO
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from uuid_utils import uuid7

from shared_db import async_engine
from shared_utils.logger import get_logger


logger = get_logger("pop/actors")


ORIGIN_URL = (
    "https://api.github.com/repos/LABCapital-VD/IIP-Cuadernos-Jupyter/contents/"
    "Gestión/Migración a DB/output/actors.actors_template.csv"
)

LOCAL_ACTORS_FILE = os.getenv(
    "ACTORS_FILE",
    "/api/populator/pops/jhonatan/actors.actors_template.csv",
)

LOCAL_SEGMENTS_FILE = os.getenv(
    "ACTOR_SEGMENTS_FILE",
    "/api/populator/pops/jhonatan/actors.actor_segments_template.csv",
)

SOURCE = os.getenv("POPULATOR_SOURCE", "local").lower()


def clean_text(value):
    """Convierte NaN, cadenas vacías y espacios en None."""
    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def normalize_key(value):
    """Normaliza texto para cruces robustos por label."""
    value = clean_text(value)

    if value is None:
        return None

    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"\s+", " ", value).strip()

    return value


def parse_int_or_none(value):
    """Convierte valores enteros del CSV; vacío queda como NULL."""
    value = clean_text(value)

    if value is None:
        return None

    value = value.replace(".", "").replace(",", "").strip()

    if value == "":
        return None

    try:
        return int(value)
    except ValueError:
        raise ValueError(f"No se pudo convertir a entero el valor: {value}")


def is_uuid(value) -> bool:
    value = clean_text(value)

    if value is None:
        return False

    try:
        UUID(value)
        return True
    except Exception:
        return False


def is_uuidv7(value) -> bool:
    value = clean_text(value)

    if value is None:
        return False

    try:
        return UUID(value).version == 7
    except Exception:
        return False


def normalize_uuidv7(value) -> str:
    """Conserva UUIDv7 si ya existe; si no, genera uno nuevo."""
    value = clean_text(value)

    if is_uuidv7(value):
        return str(UUID(value))

    return str(uuid7())


def truncate_text(value, max_length: int | None):
    """Recorta texto solo si la columna tiene longitud máxima."""
    value = clean_text(value)

    if value is None:
        return None

    if max_length is None:
        return value

    if len(value) <= max_length:
        return value

    return value[:max_length]


def read_csv_auto(path_or_text: str, from_text: bool = False) -> pd.DataFrame:
    """Lee CSV local o remoto tolerando separador y codificación."""
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


async def load_actors_dataframe(gh) -> pd.DataFrame:
    """Carga entidades desde local por defecto o desde GitHub si se activa."""
    if SOURCE == "github":
        logger.info("Loading actors from GitHub...")
        csv_text = await gh.get_raw_text(ORIGIN_URL)
        return read_csv_auto(csv_text, from_text=True)

    logger.info(f"Loading actors from local file: {LOCAL_ACTORS_FILE}")
    return read_csv_auto(LOCAL_ACTORS_FILE, from_text=False)


def load_segments_dataframe() -> pd.DataFrame:
    """Carga sectores locales para mapear id antiguo -> label."""
    logger.info(f"Loading local actor_segments map from: {LOCAL_SEGMENTS_FILE}")
    return read_csv_auto(LOCAL_SEGMENTS_FILE, from_text=False)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas y corrige alias frecuentes."""
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    aliases = {
        "treusary_code": "treasury_code",
        "treasurycode": "treasury_code",
        "sigepcode": "sigep_code",
        "actorsegmentid": "actor_segment_id",
    }

    rename_map = {}

    for col in df.columns:
        key = col.lower().replace(" ", "").replace("-", "_")
        if key in aliases:
            rename_map[col] = aliases[key]

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


async def get_table_columns(conn) -> dict:
    """Trae metadatos reales de actors.actors."""
    query = text(
        """
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'actors'
          AND table_name = 'actors'
        ORDER BY ordinal_position;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    if not rows:
        raise ValueError("No se encontró la tabla actors.actors en PostgreSQL.")

    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "max_length": row["character_maximum_length"],
            "nullable": row["is_nullable"] == "YES",
        }
        for row in rows
    }


async def get_existing_segments(conn) -> tuple[set[str], dict[str, str]]:
    """Consulta sectores reales en PostgreSQL.

    Retorna:
    - set con ids reales.
    - mapa label_normalizado -> id real.
    """
    query = text(
        """
        SELECT id::text AS id, label
        FROM actors.actor_segments;
        """
    )

    result = await conn.execute(query)
    rows = result.mappings().all()

    if not rows:
        raise ValueError(
            "La tabla actors.actor_segments está vacía. "
            "Primero ejecuta 10a_seed_sectors.py."
        )

    existing_ids = set()
    key_to_real_id = {}

    for row in rows:
        real_id = clean_text(row["id"])
        label = clean_text(row["label"])
        key = normalize_key(label)

        if real_id:
            existing_ids.add(real_id)

        if real_id and key:
            key_to_real_id[key] = real_id

    return existing_ids, key_to_real_id


def prepare_segments_lookup(df_segments: pd.DataFrame) -> dict[str, str]:
    """Crea mapa id antiguo del CSV de sectores -> label normalizado."""
    df = normalize_columns(df_segments)

    required_columns = {"id", "label"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas obligatorias en actors.actor_segments_template.csv: "
            f"{sorted(missing)}"
        )

    df["id"] = df["id"].apply(clean_text)
    df["label"] = df["label"].apply(clean_text)
    df["segment_key"] = df["label"].apply(normalize_key)

    df = df[df["id"].notna() & df["segment_key"].notna()].copy()

    if df.empty:
        raise ValueError("El archivo local de sectores quedó vacío después de limpiar.")

    return dict(zip(df["id"], df["segment_key"]))


def prepare_actors(df_actors: pd.DataFrame, db_columns: dict) -> pd.DataFrame:
    """Limpia, valida y deja la tabla de entidades lista para upsert."""
    df = normalize_columns(df_actors)

    required_columns = {
        "actor_segment_id",
        "label",
        "description",
        "mission",
        "vision",
        "id",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas obligatorias en actors.actors_template.csv: "
            f"{sorted(missing)}"
        )

    df = df.dropna(how="all").copy()

    for col in df.columns:
        df[col] = df[col].apply(clean_text)

    df = df[df["label"].notna()].copy()

    if df.empty:
        raise ValueError("El archivo de entidades quedó vacío después de limpiar.")

    duplicated = df[df["label"].duplicated(keep=False)]["label"].tolist()

    if duplicated:
        raise ValueError(
            f"Hay entidades duplicadas por label en el CSV: {sorted(set(duplicated))}"
        )

    # ID del actor: si viene UUIDv4 o vacío, se genera UUIDv7.
    df["id"] = df["id"].apply(normalize_uuidv7)

    # Campos numéricos: vacío queda como NULL.
    if "sigep_code" in df.columns:
        df["sigep_code"] = df["sigep_code"].apply(parse_int_or_none)

    if "treasury_code" in df.columns:
        df["treasury_code"] = df["treasury_code"].apply(parse_int_or_none)

    # Si la base NO permite NULL en alguno de estos campos, se rellena.
    # Si la base sí permite NULL, se conserva None como pidió el usuario.
    for col in ["description", "mission", "vision"]:
        if col in db_columns and not db_columns[col]["nullable"]:
            if col == "description":
                df[col] = df[col].fillna("Sin descripción registrada.")
            elif col == "mission":
                df[col] = df[col].fillna(df["description"])
                df[col] = df[col].fillna("Sin misión registrada.")
            elif col == "vision":
                df[col] = df[col].fillna("Sin visión registrada.")

    # Ajuste de longitudes según la base real.
    for col in df.columns:
        if col not in db_columns:
            continue

        max_length = db_columns[col]["max_length"]

        if max_length is not None:
            if col == "label":
                too_long = df[df[col].notna() & (df[col].str.len() > max_length)][col].tolist()
                if too_long:
                    raise ValueError(
                        f"Hay labels con más de {max_length} caracteres: {too_long}"
                    )
            else:
                over_count = df[df[col].notna() & (df[col].str.len() > max_length)].shape[0]
                if over_count > 0:
                    logger.warning(
                        f"{over_count} valores de {col} superaban {max_length} caracteres. "
                        "Se recortaron para evitar error en PostgreSQL."
                    )

                df[col] = df[col].apply(lambda x: truncate_text(x, max_length))

    return df


def resolve_actor_segment_ids(
    df_actors: pd.DataFrame,
    csv_segment_id_to_key: dict[str, str],
    existing_segment_ids: set[str],
    segment_key_to_real_id: dict[str, str],
) -> pd.DataFrame:
    """Resuelve actor_segment_id contra el id real en actors.actor_segments."""
    df = df_actors.copy()

    resolved_ids = []
    unresolved = []

    for index, row in df.iterrows():
        original_segment_id = clean_text(row.get("actor_segment_id"))

        # Caso 1: el ID del CSV ya coincide con un ID real de PostgreSQL.
        if original_segment_id in existing_segment_ids:
            resolved_ids.append(original_segment_id)
            continue

        # Caso 2: el ID del CSV es antiguo. Buscamos su sector por el CSV local.
        segment_key = csv_segment_id_to_key.get(original_segment_id)

        # Caso 3: con el label normalizado buscamos el ID real en PostgreSQL.
        real_segment_id = segment_key_to_real_id.get(segment_key)

        if real_segment_id:
            resolved_ids.append(real_segment_id)
            continue

        unresolved.append(
            {
                "row": int(index),
                "actor_label": row.get("label"),
                "actor_segment_id_csv": original_segment_id,
                "segment_key_from_csv": segment_key,
            }
        )
        resolved_ids.append(None)

    if unresolved:
        raise ValueError(
            "No fue posible resolver actor_segment_id para algunas entidades. "
            f"Total sin resolver: {len(unresolved)}. "
            f"Muestra: {unresolved[:20]}"
        )

    df["actor_segment_id"] = resolved_ids

    return df


async def upsert_actors(conn, df: pd.DataFrame, db_columns: dict) -> None:
    """Inserta o actualiza actors.actors usando label como clave natural."""
    preferred_columns = [
        "id",
        "actor_segment_id",
        "sigep_code",
        "treasury_code",
        "initials",
        "label",
        "description",
        "mission",
        "vision",
    ]

    insert_columns = [
        col for col in preferred_columns
        if col in db_columns and col in df.columns
    ]

    required_insert = {"id", "actor_segment_id", "label"}

    missing_required = required_insert - set(insert_columns)

    if missing_required:
        raise ValueError(
            f"No se pueden insertar entidades. Faltan columnas requeridas en la base/CSV: "
            f"{sorted(missing_required)}"
        )

    def value_expression(col: str) -> str:
        if col in {"id", "actor_segment_id", "contact_person_id"}:
            return f"CAST(:{col} AS uuid)"
        return f":{col}"

    columns_sql = ", ".join(insert_columns)
    values_sql = ", ".join(value_expression(col) for col in insert_columns)

    update_columns = [
        col for col in insert_columns
        if col != "id"
    ]

    update_sql = ", ".join(
        f"{col} = EXCLUDED.{col}"
        for col in update_columns
    )

    sql = text(
        f"""
        INSERT INTO actors.actors ({columns_sql})
        VALUES ({values_sql})
        ON CONFLICT (label)
        DO UPDATE SET
            {update_sql};
        """
    )

    inserted_or_updated = 0

    for _, row in df.iterrows():
        params = {}

        for col in insert_columns:
            value = row.get(col)

            if pd.isna(value):
                value = None

            params[col] = value

        await conn.execute(sql, params)
        inserted_or_updated += 1

    logger.info(f"Actors upsert completed: {inserted_or_updated} rows inserted/updated.")


async def upgrade(gh, api) -> None:
    """Carga y actualiza entidades directamente en PostgreSQL."""
    logger.info("Starting actors direct upsert population...")

    try:
        df_actors_raw = await load_actors_dataframe(gh)
        df_segments_raw = load_segments_dataframe()

        logger.info(f"Raw actors rows loaded: {len(df_actors_raw)}")
        logger.info(f"Raw local actor_segments rows loaded: {len(df_segments_raw)}")

        async with async_engine.begin() as conn:
            db_columns = await get_table_columns(conn)

            logger.info(f"actors.actors columns detected: {sorted(db_columns.keys())}")

            csv_segment_id_to_key = prepare_segments_lookup(df_segments_raw)

            existing_segment_ids, segment_key_to_real_id = await get_existing_segments(conn)

            logger.info(f"Existing actor_segments ids in DB: {len(existing_segment_ids)}")
            logger.info(f"Existing actor_segments label map in DB: {len(segment_key_to_real_id)}")

            df_actors = prepare_actors(df_actors_raw, db_columns=db_columns)

            df_actors = resolve_actor_segment_ids(
                df_actors=df_actors,
                csv_segment_id_to_key=csv_segment_id_to_key,
                existing_segment_ids=existing_segment_ids,
                segment_key_to_real_id=segment_key_to_real_id,
            )

            logger.info("actor_segment_id resolved successfully for all actors.")

            await upsert_actors(
                conn=conn,
                df=df_actors,
                db_columns=db_columns,
            )

        logger.info("Actors direct upsert population finished successfully.")

    except Exception as e:
        logger.error(f"Failed to run actors direct upsert: {e}")
        raise