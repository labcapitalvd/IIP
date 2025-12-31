"""Poblado de relational operators"""

from enum import Enum

from shared_db import SessionSync
from shared_utils.logging import get_logger

from models import RelationalOperator


logger = get_logger("seed/relational_operators")


class Types(Enum):
    EQUAL = "Dos valores son iguales."
    NOT_EQUAL = "Dos valores son diferentes."
    IS = "Un valor es igual a otro."
    IS_NOT = "Un valor no es igual a otro."
    GREATER_THAN = "Un valor es mayor que otro."
    LESS_THAN = "Un valor es menor que otro."
    GREATER_THAN_OR_EQUAL = "Un valor es mayor o igual que otro."
    LESS_THAN_OR_EQUAL = "Un valor es menor o igual que otro."

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = (
                session.query(RelationalOperator).filter_by(label=type.label).first()
            )
            if exists:
                continue  # Skip this one
            session.add(
                RelationalOperator(
                    label=type,
                    description=type.description,
                )
            )
        session.commit()
