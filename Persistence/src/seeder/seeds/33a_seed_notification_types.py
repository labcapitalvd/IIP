"""Poblado de notification types"""

from shared.db import SessionSync
from shared.models import NotificationType
from shared.utils.logger import get_logger

from shared.enums import NotificationTypesEnum as Types

logger = get_logger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        for type in Types:
            exists: NotificationType | None = (
                session.query(NotificationType).filter_by(label=type.label).first()
            )
            if exists:
                logger.debug(f"{type} already exists in NotificationType")
                skipped_count += 1
                continue  # Skip this one
            session.add(
                NotificationType(
                    code=type.code,
                    label=type.label,
                    description=type.description,
                )
            )
            logger.debug(f"{type} added to table NotificationType")
            added_count += 1
        session.commit()
    logger.debug(f"Seed complete: {added_count} added, {skipped_count} skipped.")
