"""Poblado de submission status types"""

from shared.db import SessionSync
from shared.enums import SubmissionStatusesEnum as Types
from shared.models import SubmissionStatusType
from shared.utils.logger import getLogger
from sqlalchemy import select

logger = getLogger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing status type labels in 1 single query
        existing_labels = set(session.scalars(select(SubmissionStatusType.label)).all())

        new_records: list[SubmissionStatusType] = []

        for status_type in Types:
            if status_type.label in existing_labels:
                logger.debug(
                    f"SubmissionStatusType '{status_type.label}' already exists"
                )
                skipped_count += 1
                continue

            new_records.append(
                SubmissionStatusType(
                    code=status_type.code,
                    label=status_type.label,
                    description=status_type.description,
                )
            )
            logger.debug(f"Queued '{status_type.label}' for SubmissionStatusType")
            added_count += 1

        # Bulk insert all new status types at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.debug(
        f"SubmissionStatusType seed complete: {added_count} added, {skipped_count} skipped."
    )
