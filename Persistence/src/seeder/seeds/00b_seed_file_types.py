"""Poblado de file types"""

from shared.db import SessionSync
from shared.models import FileType
from shared.utils.logger import get_logger

from shared.enums import FileTypesEnum as Types


logger = get_logger("seed/file_types")


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        for type in Types:
            exists: FileType | None = (
                session.query(FileType).filter_by(label=type.label).first()
            )
            if exists:
                logger.debug(msg=f"{type} already exists in FileType")
                skipped_count += 1
                continue  # Skip this one
            session.add(
                FileType(
                    code=type.code,
                    label=type.label,
                    mime_type=type.mime_type,
                    extension=type.extension,
                    category=type.category,
                    max_size=type.max_size,
                )
            )
            logger.debug(f"{type} added to table FileType")
            added_count += 1
        session.commit()
    logger.debug(f"Seed complete: {added_count} added, {skipped_count} skipped.")
