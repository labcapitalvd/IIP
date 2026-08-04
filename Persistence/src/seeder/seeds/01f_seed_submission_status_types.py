"""Poblado de submission status types"""

from shared.db import SessionSync
from shared.utils.logger import get_logger


from shared.models import SubmissionStatusType
from shared.enums import SubmissionStatusesEnum as Types

logger = get_logger("seed/submission_status_types")


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        for type in Types:
            exists: SubmissionStatusType | None = (
                session.query(SubmissionStatusType).filter_by(label=type.label).first()
            )
            if exists:
                logger.debug(f"{type} already exists in SubmissionStatusType")
                skipped_count += 1
                continue  # Skip this one
            session.add(
                SubmissionStatusType(
                    code=type.code,
                    label=type.label,
                    description=type.description,
                )
            )
            logger.debug(f"{type} added to table SubmissionStatusType")
            added_count += 1
        session.commit()
    logger.debug(f"Seed complete: {added_count} added, {skipped_count} skipped.")
