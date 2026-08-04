"""Poblado de submission status types"""

from shared.db import SessionSync
from shared.utils.logger import get_logger


from shared.models import SubmissionStatusType
from shared.enums import SubmissionStatusesEnum as Types

logger = get_logger("seed/submission_status_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists: SubmissionStatusType | None = (
                session.query(SubmissionStatusType).filter_by(label=type.label).first()
            )
            if exists:
                logger.info(f"{type} already exists in SubmissionStatusType")
                continue  # Skip this one
            session.add(
                SubmissionStatusType(
                    code=type.code,
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table SubmissionStatusType")
        session.commit()
