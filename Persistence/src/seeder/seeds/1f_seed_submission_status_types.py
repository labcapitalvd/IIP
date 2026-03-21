"""Poblado de submission status types"""

from shared_db import SessionSync
from shared_utils.logger import get_logger

from models import SubmissionStatusType, SubmissionStatusesEnum as Types


logger = get_logger("seed/submission_status_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = (
                session.query(SubmissionStatusType).filter_by(label=type.label).first()
            )
            if exists:
                logger.info(f"{type} already exists in SubmissionStatusType")
                continue  # Skip this one
            session.add(
                SubmissionStatusType(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table SubmissionStatusType")
        session.commit()
