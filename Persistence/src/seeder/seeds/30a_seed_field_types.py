"""Poblado de tipos de campos (FieldType)"""

from shared.db import SessionSync
from shared.enums import FieldTypesEnum as Types
from shared.models import FieldType
from shared.utils.logger import getLogger
from sqlalchemy import select

logger = getLogger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing field type codes in 1 single query
        existing_codes = set(session.scalars(select(FieldType.code)).all())

        new_records: list[FieldType] = []

        for field_type in Types:
            if field_type.code in existing_codes:
                logger.debug(
                    f"FieldType '{field_type.code}' ya existe en la base de datos"
                )
                skipped_count += 1
                continue

            new_records.append(
                FieldType(
                    code=field_type.code,
                    label=field_type.label,
                    description=field_type.description,
                )
            )
            logger.debug(f"Queued '{field_type.code}' for FieldType")
            added_count += 1

        # Bulk insert all new field types at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.debug(
        f"FieldType seed complete: {added_count} added, {skipped_count} skipped."
    )
