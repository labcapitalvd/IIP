"""Poblado de section types"""

from enum import Enum

from shared_db import SessionSync
from shared_utils.logger import get_logger

from models import SectionType

logger = get_logger("seed/section_types")


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
                logger.info(f"{type} already exists in SectionType")
                continue  # Skip this one
            session.add(
                SectionType(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table SectionType")
        session.commit()
