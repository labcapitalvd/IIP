import os
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
import numpy as np

from db.actors import ActorDb

from shared_utils import TextUtils


def load_results_excel(path: str = "./handlers/resultados_2025.xlsx") -> pd.DataFrame:
    """Safely load the Excel file and sanitize for JSON serialization."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Results file not found: {path}")

    df = pd.read_excel(path)

    df = df.replace([np.nan, np.inf, -np.inf, pd.NA, pd.NaT], None)
    return df


safe_df = load_results_excel()


class ResultHandler:
    def __init__(self, db: AsyncSession, current_user: UUID):
        self.db = db

        self.textutils = TextUtils()
        self.actorondb = ActorDb(self.db)

    async def ResultRead(self, id: UUID, detailed: bool = False):
        actor = await self.actorondb.get_actor_entry(id=id)
        actor_name = actor.name

        filtered = safe_df.copy()

        filtered = filtered[
            filtered["Entidad"].astype(str).str.strip().str.lower()
            == actor_name.strip().lower()
        ]

        return filtered.to_dict(orient="records")

    async def ResultReadAll(self, detailed: bool = False):
        return safe_df.to_dict(orient="records")
