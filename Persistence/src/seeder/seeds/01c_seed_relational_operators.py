"""Poblado de relational operators"""

from shared.db import SessionSync
from shared.enums import RelationalOperatorsEnum as Types
from shared.models import RelationalOperator
from shared.utils.logger import getLogger
from sqlalchemy import select

logger = getLogger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing relational operator labels in 1 single query
        existing_labels = set(session.scalars(select(RelationalOperator.label)).all())

        new_records: list[RelationalOperator] = []

        for op_type in Types:
            if op_type.label in existing_labels:
                logger.debug(f"RelationalOperator '{op_type.label}' already exists")
                skipped_count += 1
                continue

            new_records.append(
                RelationalOperator(
                    code=op_type.code,
                    label=op_type.label,
                    description=op_type.description,
                )
            )
            logger.debug(f"Queued '{op_type.label}' for RelationalOperator")
            added_count += 1

        # Bulk insert all new relational operators at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.debug(
        f"RelationalOperator seed complete: {added_count} added, {skipped_count} skipped."
    )
