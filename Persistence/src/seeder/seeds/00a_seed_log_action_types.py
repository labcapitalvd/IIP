"""Poblado de log action types"""

from shared.db import SessionSync
from shared.models import LogActionType
from shared.utils.logger import get_logger

from shared.enums import LogActionTypesEnum as Types


logger = get_logger("seed/log_action_types")


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        for type in Types:
            exists: LogActionType | None = (
                session.query(LogActionType).filter_by(label=type.label).first()
            )
            if exists:
                logger.info(msg=f"{type} already exists in LogActionType")
                skipped_count += 1
                continue  # Skip this one
            session.add(
                LogActionType(
                    code=type.label,
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table LogActionType")
            added_count += 1
        session.commit()
    logger.info(f"Seed complete: {added_count} added, {skipped_count} skipped.")
