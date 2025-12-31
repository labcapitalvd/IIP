"""Poblado de notification types"""

from enum import Enum

from shared_db import SessionSync
from shared_models import NotificationType
from shared_utils.logging import get_logger


logger = get_logger("seed/notification_types")


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
