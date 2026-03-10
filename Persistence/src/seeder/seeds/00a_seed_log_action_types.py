"""Poblado de log action types"""

from shared_db import SessionSync
from shared_models import LogActionType
from shared_utils.logger import get_logger

from models import LogActionTypesEnum as Types


logger = get_logger("seed/log_action_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(LogActionType).filter_by(label=type.label).first()
            if exists:
                logger.info(f"{type} already exists in LogActionType")
                continue  # Skip this one
            session.add(
                LogActionType(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table LogActionType")
        session.commit()
