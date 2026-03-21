"""Poblado de roles"""

from shared_db import SessionSync
from shared_models import Role
from shared_utils.logger import get_logger

from models import RolesEnum as Types

logger = get_logger("seed/roles")


def upgrade() -> None:
    with SessionSync() as session:
        for type in Types:
            exists = session.query(Role).filter_by(label=type.label).first()
            if exists:
                logger.info(f"{type} already exists in Role") 
                continue  # Skip this one
            session.add(
                Role(
                    label=type.label,
                    description=type.description,
                )
            )
            logger.info(f"{type} added to table Role")
        session.commit()
