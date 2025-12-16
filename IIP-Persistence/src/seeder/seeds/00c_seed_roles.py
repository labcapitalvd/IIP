"""Poblado de roles"""
import os
from enum import Enum

import logging

from shared_db import SessionSync

from shared_models import Role


LOGLEVEL = os.environ["LOGLEVEL"].lower() in (
    "debug",
    "info",
    "warning",
    "error",
    "critical",
)

logger = logging.getLogger("seed/roles")
logger.setLevel(LOGLEVEL)


class Types(Enum):
    OWNER = "owner"  # Full control over the submission or actor
    CONTRIBUTOR = "contributor"  # Can fill/edit forms, upload files, etc.
    REVIEWER = "reviewer"  # Can comment or suggest changes
    APPROVER = "approver"  # Can finalize and submit
    OBSERVER = "observer"  # Read-only access

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(Role).filter_by(label=type.label).first()
            if exists:
                continue  # Skip this one
            session.add(
                Role(
                    label=type,
                    description=type.description,
                )
            )
        session.commit()



