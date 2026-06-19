"""Poblado de log action types"""

from shared.db import SessionSync
from shared.models import LogActionType
from shared.utils.logger import get_logger

from shared.enums import LogActionTypesEnum as Types


logger = get_logger("seed/log_action_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists: LogActionType | None = (
                session.query(LogActionType).filter_by(label=type.label).first()
            )
            if exists:
                logger.info(msg=f"{type} already exists in LogActionType")
                continue  # Skip this one
            session.add(
                LogActionType(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table LogActionType")
        session.commit()
