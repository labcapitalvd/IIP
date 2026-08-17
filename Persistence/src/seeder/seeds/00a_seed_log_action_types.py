"""Poblado de log action types"""

from shared.db import SessionSync
from shared.enums import LogActionTypesEnum as Types
from shared.models import LogActionType
from shared.utils.logger import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing labels at once in 1 query (SQLAlchemy 2.0 style)
        existing_labels = set(session.scalars(select(LogActionType.label)).all())

        new_records: list[LogActionType] = []

        for action_type in Types:
            if action_type.label in existing_labels:
                logger.debug(f"{action_type.label} already exists in LogActionType")
                skipped_count += 1
                continue

            new_records.append(
                LogActionType(
                    code=action_type.label,
                    label=action_type.label,
                    description=action_type.description,
                )
            )
            logger.debug(f"Queued {action_type.label} for LogActionType")
            added_count += 1

        # Bulk insert all missing records in a single call
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.debug(
        f"LogActionType seed complete: {added_count} added, {skipped_count} skipped."
    )
