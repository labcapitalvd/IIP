"""Poblado de actor_segments"""

import os
import uuid
from io import StringIO

import pandas as pd

from shared_utils.logger import get_logger
from shared_schemas import ActorSegmentSchema


logger = get_logger("seed/sectors")


ORIGIN_URL = "https://api.github.com/repos/LABCapital-VD/IIP-Cuadernos-Jupyter/contents/Gestión/Migración a DB/output/00_sectores.csv"


async def upgrade(gh, api) -> None:
    """Fetches sectors CSV from GitHub, checks for existing IDs via API, and seeds missing data."""
    logger.info("Starting Sectors population...")

    try:
        csv_text = await gh.get_raw_text(ORIGIN_URL)

        df = pd.read_csv(StringIO(csv_text), sep="|")

        if df.empty:
            logger.info("Sectors file from GitHub is empty.")
            return

        df["id"] = df["id"].apply(
            lambda x: str(uuid.UUID(str(x))) if pd.notnull(x) else None
        )

        try:
            existing_entries = await api.get_entries(f"/actor_segments/all")
            existing_ids = {entry["id"] for entry in existing_entries if "id" in entry}
        except Exception as e:
            logger.warning(
                f"Could not fetch existing entries from /all, assuming empty table. Error: {e}"
            )
            existing_ids = set()

        df_to_insert = df[~df["id"].isin(existing_ids)]
        print((df_to_insert))

        if not df_to_insert.empty:
            records_to_send = df_to_insert.to_dict(orient="records")
            print((records_to_send))

            await api.create_multiple_entries(
                endpoint=f"/actor_segments/new", schema=ActorSegmentSchema, data_list=records_to_send
            )
        else:
            logger.info(f"No new rows to insert for /actor_segments/all")

    except Exception as e:
        logger.error(f"Failed to run sectors upgrade: {e}")
        raise e
