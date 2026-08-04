"""Poblado de permisos atómicos y granulares (Permission)"""

from shared.db import SessionSync
from shared.enums import PermissionsEnum  # Assuming you have an enum for permissions
from shared.models import Permission
from shared.utils.logger import get_logger

logger = get_logger("seed/permissions")


def upgrade() -> None:
    with SessionSync() as session:
        for perm_enum in PermissionsEnum:
            exists = session.query(Permission).filter_by(code=perm_enum.code).first()
            if exists:
                logger.info(f"Permission '{perm_enum.code}' already exists")
                continue

            session.add(
                Permission(
                    key=perm_enum.key,
                    code=perm_enum.code,
                    label=perm_enum.label,
                    description=perm_enum.description,
                )
            )
            logger.info(f"Permission '{perm_enum.code}' added to table")

        session.commit()
