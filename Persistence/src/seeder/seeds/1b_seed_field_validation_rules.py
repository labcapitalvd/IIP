"""Poblado de field validation rules"""

from enum import Enum

from shared_db import SessionSync
from shared_utils.logger import get_logger

from models import ValidationType


logger = get_logger("seed/field_validation_rules")


class Types(Enum):
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    REGEX = "regex"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(ValidationType).filter_by(label=type.label).first()
            if exists:
                continue  # Skip this one
            session.add(
                ValidationType(
                    label=type,
                    description=type.description,
                )
            )
        session.commit()
