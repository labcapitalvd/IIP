"""Poblado de log action types"""

from enum import Enum

from shared_db import SessionSync
from shared_models import LogActionType
from shared_utils import get_logger


logger = get_logger("seed/log_action_types")


class Types(Enum):
    CREATE = "Se crea una nueva entrada."
    UPDATE = "Se actualiza una entrada."
    DELETE = "Se elimina una entrada."
    GRADE = "Se califica una entrada."
    UPLOAD = "Se carga un archivo."

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(LogActionType).filter_by(label=type.label).first()
            if exists:
                continue  # Skip this one
            session.add(
                LogActionType(
                    label=type,
                    description=type.description,
                )
            )
        session.commit()
