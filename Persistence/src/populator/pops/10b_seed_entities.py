"""Poblado de actors"""

import os
import uuid
from io import StringIO

import pandas as pd

from shared_utils.logger import get_logger
from shared_schemas import ActorSegmentSchema, ActorSchema


logger = get_logger("seed/sectors")


ORIGIN_URL = "https://api.github.com/repos/LABCapital-VD/IIP-Cuadernos-Jupyter/contents/Gestión/Migración a DB/output/01_entidades.csv"

async def upgrade(gh, api) -> None:
    """Fetches sectors CSV from GitHub, checks for existing IDs via API, and seeds missing data."""
    logger.info("Starting Sectors population...")

    try:
        csv_text = await gh.get_raw_text(ORIGIN_URL)

        df = pd.read_csv(StringIO(csv_text), sep="|")

        if df.empty:
            logger.info("Actors file from GitHub is empty.")
            return

        df["id"] = df["id"].apply(
            lambda x: str(uuid.UUID(str(x))) if pd.notnull(x) else None
        )

        try:
            existing_actor_segments = await api.get_entries(f"/actor_segments/all")
            existing_actor_segment_ids = {entry["id"] for entry in existing_actor_segments if "id" in entry}
        except Exception as e:
            logger.warning(
                f"Could not fetch existing entries from /actor_segments/all, assuming empty table. Error: {e}"
            )
            existing_actor_segment_ids = set()

        try:
            existing_actors = await api.get_entries(f"/actors/all")
            existing_actor_ids = {entry["id"] for entry in existing_actors if "id" in entry}
        except Exception as e:
            logger.warning(
                f"Could not fetch existing entries from /actors/all, assuming empty table. Error: {e}"
            )
            existing_actor_ids = set()

        df_to_insert = df[~df["id"].isin(existing_actor_ids)]

        if not df_to_insert.empty:
            records_to_send = df_to_insert.to_dict(orient="records")

            await api.create_multiple_entries(
                endpoint=f"/actors/new", schema=ActorSchema, data_list=records_to_send
            )
        else:
            logger.info(f"No new rows to insert for /actors/new")

    except Exception as e:
        logger.error(f"Failed to run sectors upgrade: {e}")
        raise e
