"""Poblado de roles de recursos ReBAC (ResourceRole)"""

from shared.db import SessionSync
from shared.enums import ResourceRolesEnum
from shared.models import ResourceRole
from shared.utils.logger import get_logger

logger = get_logger("seed/resource_roles")


def upgrade() -> None:
    with SessionSync() as session:
        for role_enum in ResourceRolesEnum:
            exists = session.query(ResourceRole).filter_by(code=role_enum.code).first()
            if exists:
                logger.info(f"ResourceRole '{role_enum.code}' already exists")
                continue

            session.add(
                ResourceRole(
                    code=role_enum.code,
                    label=role_enum.label,
                    description=role_enum.description,
                )
            )
            logger.info(f"ResourceRole '{role_enum.code}' added to table")

        session.commit()
