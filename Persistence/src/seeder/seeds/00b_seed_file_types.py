"""Poblado de file types"""

from shared.db import SessionSync
from shared.models import FileType
from shared.utils.logger import get_logger

from shared.enums import FileTypesEnum as Types


logger = get_logger("seed/file_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists: FileType | None = (
                session.query(FileType).filter_by(label=type.label).first()
            )
            if exists:
                logger.info(msg=f"{type} already exists in FileType")
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
            logger.info(f"{type} added to table FileType")
        session.commit()
