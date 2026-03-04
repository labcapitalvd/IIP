"""Poblado de comment types"""

from shared_db import SessionSync
from shared_models import CommentType
from shared_utils.logger import get_logger

from models import CommentTypesEnum as Types

logger = get_logger("seed/comment_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(CommentType).filter_by(label=type.label).first()
            if exists:
                logger.info(f"{type} already exists in CommentType")
                continue  # Skip this one
            session.add(
                CommentType(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table CommentType")
        session.commit()
