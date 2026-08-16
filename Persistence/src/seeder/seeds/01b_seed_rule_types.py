"""Poblado de field validation rules"""

from shared.db import SessionSync
from shared.enums import RuleTypesEnum as Types
from shared.models import RuleType
from shared.utils.logger import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing rule type labels in 1 single query
        existing_labels = set(session.scalars(select(RuleType.label)).all())

        new_records: list[RuleType] = []

        for rule_type in Types:
            if rule_type.label in existing_labels:
                logger.debug(f"RuleType '{rule_type.label}' already exists")
                skipped_count += 1
                continue

            new_records.append(
                RuleType(
                    code=rule_type.code,
                    label=rule_type.label,
                    description=rule_type.description,
                )
            )
            logger.debug(f"Queued '{rule_type.label}' for RuleType")
            added_count += 1

        # Bulk insert all new rule types at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.info(
        f"RuleType seed complete: {added_count} added, {skipped_count} skipped."
    )
