"""Poblado de field validation rules"""

from shared_db import SessionSync
from shared_utils.logger import get_logger

from models import RuleType, RuleTypesEnum as Types


logger = get_logger("seed/field_validation_rules")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(RuleType).filter_by(label=type.label).first()
            if exists:
                logger.info(f"{type} already exists in RuleType")
                continue  # Skip this one
            session.add(
                RuleType(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table RuleType")
        session.commit()
