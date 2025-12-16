"""Poblado de section types"""
import os
import logging
from enum import Enum

from shared_db import SessionSync
from models import SectionType


LOGLEVEL = os.environ["LOGLEVEL"].lower() in (
    "debug",
    "info",
    "warning",
    "error",
    "critical",
)
logger = logging.getLogger("seed/section_types")
logger.setLevel(LOGLEVEL)


class Types(Enum):
    COMPONENTE = "Representa a un componente."
    VARIABLE = "Representa a una variable."
    INDICADOR = "Representa a un indicador."

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(SectionType).filter_by(label=type.label).first()
            if exists:
                continue  # Skip this one
            session.add(
                SectionType(
                    label=type,
                    description=type.description,
                )
            )
        session.commit()



