"""Poblado de tipos de campos (FieldType)"""

from shared.db import SessionSync
from shared.enums import FieldTypesEnum as Types
from shared.models import FieldType
from shared.utils.logger import get_logger

logger = get_logger("seed/field_types")


def upgrade() -> None:
    with SessionSync() as session:
        for item in Types:
            exists: FieldType | None = (
                session.query(FieldType).filter_by(code=item.code).first()
            )
            if exists:
                logger.info(f"FieldType '{item.code}' ya existe en la base de datos")
                continue

            session.add(
                FieldType(
                    code=item.code,
                    label=item.label,
                    description=item.description,
                )
            )
            logger.info(f"FieldType '{item.code}' añadido a la tabla")

        session.commit()
