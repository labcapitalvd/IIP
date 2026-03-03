"""Poblado de actors"""

import os
import uuid
from io import StringIO

import pandas as pd
import requests
from sqlalchemy import UUID as UUIDType

from shared_db import sync_engine
from shared_utils.logger import get_logger

from models.targets import TargetTable


logger = get_logger("seed/entities")


TABLE = TargetTable.ACTORS.table
SCHEMA = TargetTable.ACTORS.schema
ORIGIN_URL = "https://api.github.com/repos/LABCapital-VD/IIP-Cuadernos-Jupyter/contents/Gestión/Migración a DB/output/01_entidades.csv"

GITHUB_TOKEN_FILE = "/run/secrets/github_token_seeds"
if not os.path.exists(GITHUB_TOKEN_FILE):
    raise FileNotFoundError(f"GITHUB_TOKEN_FILE file not found at {GITHUB_TOKEN_FILE}")
with open(GITHUB_TOKEN_FILE, "r") as f:
    GITHUB_TOKEN = f.read().strip()

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3.raw",
}
r = requests.get(ORIGIN_URL, headers=headers)
r.raise_for_status()  # fail if not 200


def upgrade() -> None:
    df = pd.read_csv(StringIO(r.text), sep="|")

    rename_map = {
        "sector_id": "actor_segment_id",
    }

    df = df.rename(columns=rename_map)

    df["id"] = df["id"].apply(lambda x: uuid.UUID(str(x)) if pd.notnull(x) else None)
    if "actor_segment_id" in df.columns:
        df["actor_segment_id"] = df["actor_segment_id"].apply(
            lambda x: uuid.UUID(str(x)) if pd.notnull(x) else None
        )

    query = f'SELECT id FROM "{SCHEMA}"."{TABLE}"'
    existing_ids = pd.read_sql(query, sync_engine)["id"].tolist()

    df_to_insert = df[~df["id"].isin(existing_ids)]

    if not df_to_insert.empty:
        df_to_insert.to_sql(
            TABLE,
            sync_engine,
            schema=SCHEMA,
            if_exists="append",
            index=False,
            dtype={"id": UUIDType(), "actor_segment_id": UUIDType()},  # type: ignore[arg-type]
        )
        logger.info(f"Inserted {len(df_to_insert)} new rows into {SCHEMA}.{TABLE}")
    else:
        logger.info(f"No new rows to insert for {SCHEMA}.{TABLE}")
