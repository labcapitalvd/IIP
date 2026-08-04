"""Poblado de relational operators"""

from shared.db import SessionSync
from shared.utils.logger import get_logger

from shared.models import RelationalOperator
from shared.enums import RelationalOperatorsEnum as Types

logger = get_logger("seed/relational_operators")


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        for type in Types:
            exists: RelationalOperator | None = (
                session.query(RelationalOperator).filter_by(label=type.label).first()
            )
            if exists:
                logger.info(f"{type} already exists in RelationalOperator")
                skipped_count += 1
                continue  # Skip this one
            session.add(
                RelationalOperator(
                    code=type.code,
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table RelationalOperator")
            added_count += 1
        session.commit()
    logger.info(f"Seed complete: {added_count} added, {skipped_count} skipped.")
