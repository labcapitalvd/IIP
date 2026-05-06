"""Poblado de field types"""

from shared_db import SessionSync
from shared_utils.logger import get_logger


from shared_models import FieldType
from shared_enums import FieldTypesEnum as Types

logger = get_logger("seed/field_types")


def upgrade() -> None:
    with SessionSync() as session:
        for tier in Types:
            exists: FieldType | None = (
                session.query(FieldType).filter_by(label=tier.label).first()
            )
            if exists:
                logger.info(f"{type} already exists in FieldType")
                continue  # Skip this one
            session.add(
                FieldType(
                    label=tier.label,
                    description=tier.description,
                )
            )
            logger.info(f"{type} added to table FieldType")
        session.commit()
