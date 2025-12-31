"""Poblado de form_versions"""

import os
import uuid
from io import StringIO

import pandas as pd
import requests
from sqlalchemy.dialects.postgresql import UUID as UUIDType

from shared_db import merge_enums, sync_engine
from shared_models.targets import TargetTable as TargetTableBase
from shared_utils.logging import get_logger

from models.targets import TargetTable as TargetTableApp

TargetTable = merge_enums("TargetTable", TargetTableBase, TargetTableApp)


logger = get_logger("seed/forms")



TABLE = TargetTable.FORMS.table
SCHEMA = TargetTable.FORMS.schema
ORIGIN_URL = "https://raw.githubusercontent.com/LABCapital-VD/IIP-Cuadernos-Jupyter/main/Gesti%C3%B3n/Migraci%C3%B3n%20a%20DB/output/00_indices.csv"

GITHUB_TOKEN_FILE = "/run/secrets/github_token"
if not os.path.exists(GITHUB_TOKEN_FILE):
    raise FileNotFoundError(f"GITHUB_TOKEN_FILE file not found at {GITHUB_TOKEN_FILE}")
with open(GITHUB_TOKEN_FILE, "r") as f:
    GITHUB_TOKEN = f.read().strip()

headers = {"Authorization": f"token {GITHUB_TOKEN}"}
r = requests.get(ORIGIN_URL, headers=headers)
r.raise_for_status()  # fail if not 200


def upgrade() -> None:
    df = pd.read_csv(StringIO(r.text), sep="|")

    df["id"] = df["id"].apply(lambda x: uuid.UUID(str(x)) if pd.notnull(x) else None)

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
            dtype={"id": UUIDType()},  # type: ignore[arg-type]
        )
        logger.info(f"Inserted {len(df_to_insert)} new rows into {SCHEMA}.{TABLE}")
    else:
        logger.info(f"No new rows to insert for {SCHEMA}.{TABLE}")
