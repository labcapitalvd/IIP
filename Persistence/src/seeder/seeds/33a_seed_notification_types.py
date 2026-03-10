"""Poblado de notification types"""

from shared_db import SessionSync
from shared_models import NotificationType
from shared_utils.logger import get_logger

from models import NotificationTypesEnum as Types

logger = get_logger("seed/notification_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(NotificationType).filter_by(label=type.label).first()
            if exists:
                logger.info(f"{type} already exists in NotificationType")
                continue  # Skip this one
            session.add(
                NotificationType(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table NotificationType")
        session.commit()
