"""Poblado de relational operators"""

from shared_db import SessionSync
from shared_utils.logger import get_logger

from models import RelationalOperator, RelationalOperatorsEnum as Types


logger = get_logger("seed/relational_operators")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = (
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
