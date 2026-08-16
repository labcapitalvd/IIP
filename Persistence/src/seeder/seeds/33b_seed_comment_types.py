"""Poblado de comment types"""

from shared.db import SessionSync
from shared.enums import CommentTypesEnum as Types
from shared.models import CommentType
from shared.utils.logger import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing comment type labels in 1 single query
        existing_labels = set(session.scalars(select(CommentType.label)).all())

        new_records: list[CommentType] = []

        for comment_type in Types:
            if comment_type.label in existing_labels:
                logger.debug(f"CommentType '{comment_type.label}' already exists")
                skipped_count += 1
                continue

            new_records.append(
                CommentType(
                    code=comment_type.code,
                    label=comment_type.label,
                    description=comment_type.description,
                )
            )
            logger.debug(f"Queued '{comment_type.label}' for CommentType")
            added_count += 1

        # Bulk insert all new comment types at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.info(
        f"CommentType seed complete: {added_count} added, {skipped_count} skipped."
    )
