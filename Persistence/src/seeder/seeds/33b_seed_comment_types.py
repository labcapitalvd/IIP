"""Poblado de comment types"""

from shared.db import SessionSync
from shared.models import CommentType
from shared.utils.logger import get_logger

from shared.enums import CommentTypesEnum as Types

logger = get_logger("seed/comment_types")


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        for type in Types:
            exists: CommentType | None = (
                session.query(CommentType).filter_by(label=type.label).first()
            )
            if exists:
                logger.debug(f"{type} already exists in CommentType")
                skipped_count += 1
                continue  # Skip this one
            session.add(
                CommentType(
                    code=type.code,
                    label=type.label,
                    description=type.description,
                )
            )
            logger.debug(f"{type} added to table CommentType")
            added_count += 1
        session.commit()
    logger.debug(f"Seed complete: {added_count} added, {skipped_count} skipped.")
