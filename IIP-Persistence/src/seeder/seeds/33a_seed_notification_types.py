"""Poblado de notification types"""
import os
import logging
from enum import Enum

from shared_db import SessionSync

from shared_models import NotificationType


LOGLEVEL = os.environ["LOGLEVEL"].lower() in (
    "debug",
    "info",
    "warning",
    "error",
    "critical",
)
logger = logging.getLogger("seed/notification_types")
logger.setLevel(LOGLEVEL)


class Types(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(NotificationType).filter_by(label=type.label).first()
            if exists:
                continue  # Skip this one
            session.add(
                NotificationType(
                    label=type,
                    description=type.description,
                )
            )
        session.commit()



