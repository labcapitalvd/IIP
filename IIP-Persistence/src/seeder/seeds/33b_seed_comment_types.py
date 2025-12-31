"""Poblado de comment types"""

from enum import Enum

from shared_db import SessionSync
from shared_models import CommentType
from shared_utils.logging import get_logger


logger = get_logger("seed/comment_types")


class Types(str, Enum):
    PUBLIC_FEEDBACK = "Alguien dio retroalimentación."
    INTERNAL_NOTE = "Una nota interna"
    REVISION_REQUEST = "Solicitud de revisión"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(CommentType).filter_by(label=type.label).first()
            if exists:
                continue  # Skip this one
            session.add(
                CommentType(
                    label=type,
                    description=type.description,
                )
            )
        session.commit()
