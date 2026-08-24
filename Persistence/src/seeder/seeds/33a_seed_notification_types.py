"""Poblado de notification types"""

from shared.db import SessionSync
from shared.enums import NotificationTypesEnum as Types
from shared.models import NotificationType
from shared.utils.logger import getLogger
from sqlalchemy import select

logger = getLogger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing notification type labels in 1 single query
        existing_labels = set(session.scalars(select(NotificationType.label)).all())

        new_records: list[NotificationType] = []

        for notif_type in Types:
            if notif_type.label in existing_labels:
                logger.debug(f"NotificationType '{notif_type.label}' already exists")
                skipped_count += 1
                continue

            new_records.append(
                NotificationType(
                    code=notif_type.code,
                    label=notif_type.label,
                    description=notif_type.description,
                )
            )
            logger.debug(f"Queued '{notif_type.label}' for NotificationType")
            added_count += 1

        # Bulk insert all new notification types at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.debug(
        f"NotificationType seed complete: {added_count} added, {skipped_count} skipped."
    )
