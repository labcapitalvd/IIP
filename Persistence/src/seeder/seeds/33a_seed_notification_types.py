"""Poblado de notification types"""

from shared.db import SessionSync
from shared.models import NotificationType
from shared.utils.logger import get_logger

from shared.enums import NotificationTypesEnum as Types

logger = get_logger("seed/notification_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists: NotificationType | None = (
                session.query(NotificationType).filter_by(label=type.label).first()
            )
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
