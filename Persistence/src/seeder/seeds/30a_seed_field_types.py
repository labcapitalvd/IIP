"""Poblado de field types"""

from enum import Enum

from shared_db import SessionSync
from shared_utils.logger import get_logger

from models import FieldType

logger = get_logger("seed/field_types")


class Types(Enum):
    BOOLEAN = "AnswerBoolean"
    CARD = "AnswerCardEntry"
    DATE = "AnswerDate"
    FILE = "AnswerFile"
    MULTI_CHOICE = "AnswerMultiChoice"
    NUMERIC = "AnswerNumeric"
    SINGLE_CHOICE = "AnswerSingleChoice"
    TEXT = "AnswerText"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name  # Use the enum member name itself


def upgrade() -> None:
    with SessionSync() as session:
        for tier in Types:
            exists = session.query(FieldType).filter_by(label=tier.label).first()
            if exists:
                continue  # Skip this one
            session.add(
                FieldType(
                    label=tier,
                    description=tier.description,
                )
            )
        session.commit()
