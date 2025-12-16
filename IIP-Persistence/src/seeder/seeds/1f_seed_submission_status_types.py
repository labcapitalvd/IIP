"""Poblado de submission status types"""
import os
import logging
from enum import Enum

from shared_db import SessionSync

from models import SubmissionStatusType


LOGLEVEL = os.environ["LOGLEVEL"].lower() in (
    "debug",
    "info",
    "warning",
    "error",
    "critical",
)
logger = logging.getLogger("seed/submission_status_types")
logger.setLevel(LOGLEVEL)


class Types(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    NEEDS_REVISION = "needs_revision"
    APPROVED = "approved"
    GRADED = "graded"
    REJECTED = "rejected"
    ASSIGNED = "assigned"
    PARTIALLY_GRADED = "partially_graded"
    AUTO_SUBMITTED = "auto_submitted"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = (
                session.query(SubmissionStatusType).filter_by(label=type.label).first()
            )
            if exists:
                continue  # Skip this one
            session.add(
                SubmissionStatusType(
                    label=type,
                    description=type.description,
                )
            )
        session.commit()



