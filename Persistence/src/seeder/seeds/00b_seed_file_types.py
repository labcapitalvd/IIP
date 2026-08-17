"""Poblado de file types"""

from shared.db import SessionSync
from shared.enums import FileTypesEnum as Types
from shared.models import FileType
from shared.utils.logger import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing labels in 1 single query
        existing_labels = set(session.scalars(select(FileType.label)).all())

        new_records: list[FileType] = []

        for file_type in Types:
            if file_type.label in existing_labels:
                logger.debug(f"{file_type.label} already exists in FileType")
                skipped_count += 1
                continue

            new_records.append(
                FileType(
                    code=file_type.code,
                    label=file_type.label,
                    mime_type=file_type.mime_type,
                    extension=file_type.extension,
                    category=file_type.category,
                    max_size=file_type.max_size,
                )
            )
            logger.debug(f"Queued {file_type.label} for FileType")
            added_count += 1

        # Bulk insert all new types at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.debug(
        f"FileType seed complete: {added_count} added, {skipped_count} skipped."
    )
