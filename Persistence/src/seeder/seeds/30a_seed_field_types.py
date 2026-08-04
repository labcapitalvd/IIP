"""Poblado de tipos de campos (FieldType)"""

from shared.db import SessionSync
from shared.enums import FieldTypesEnum as Types
from shared.models import FieldType
from shared.utils.logger import get_logger

logger = get_logger("seed/field_types")


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        for item in Types:
            exists: FieldType | None = (
                session.query(FieldType).filter_by(code=item.code).first()
            )
            if exists:
                logger.info(f"FieldType '{item.code}' ya existe en la base de datos")
                skipped_count += 1
                continue

            session.add(
                FieldType(
                    code=item.code,
                    label=item.label,
                    description=item.description,
                )
            )
            logger.info(f"FieldType '{item.code}' añadido a la tabla")
            added_count += 1
        session.commit()
    logger.info(f"Seed complete: {added_count} added, {skipped_count} skipped.")
