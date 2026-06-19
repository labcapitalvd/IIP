"""Poblado de comment types"""

from shared.db import SessionSync
from shared.models import CommentType
from shared.utils.logger import get_logger

from shared.enums import CommentTypesEnum as Types

logger = get_logger("seed/comment_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists: CommentType | None = (
                session.query(CommentType).filter_by(label=type.label).first()
            )
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
