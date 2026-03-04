"""Poblado de file types"""

from shared_db import SessionSync
from shared_models import FileType
from shared_utils.logger import get_logger

from models import FileTypesEnum as Types


logger = get_logger("seed/file_types")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(FileType).filter_by(label=type.label).first()
            if exists:
                logger.info(f"{type} already exists in FileType") 
                continue  # Skip this one
            session.add(
                FileType(
                    label=type.label,
                    mime_type=type.mime_type,
                    extension=type.extension,
                    category=type.category,
                    max_size=type.max_size,
                )
            )
            logger.info(f"{type} added to table FileType")
        session.commit()
