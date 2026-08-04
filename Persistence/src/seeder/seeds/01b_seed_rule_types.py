"""Poblado de field validation rules"""

from shared.db import SessionSync
from shared.utils.logger import get_logger

from shared.models import RuleType
from shared.enums import RuleTypesEnum as Types


logger = get_logger("seed/field_validation_rules")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists: RuleType | None = (
                session.query(RuleType).filter_by(label=type.label).first()
            )
            if exists:
                logger.info(f"{type} already exists in RuleType")
                continue  # Skip this one
            session.add(
                RuleType(
                    code=type.code,
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table RuleType")
        session.commit()
