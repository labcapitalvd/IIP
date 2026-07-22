"""Poblado de relational operators"""

from shared.db import SessionSync
from shared.utils.logger import get_logger

from shared.models import RelationalOperator
from shared.enums import RelationalOperatorsEnum as Types

logger = get_logger("seed/relational_operators")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists: RelationalOperator | None = (
                session.query(RelationalOperator).filter_by(label=type.label).first()
            )
            if exists:
                logger.info(f"{type} already exists in RelationalOperator")
                continue  # Skip this one
            session.add(
                RelationalOperator(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table RelationalOperator")
        session.commit()
