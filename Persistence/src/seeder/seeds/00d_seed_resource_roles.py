"""Poblado de roles de recursos ReBAC (ResourceRole)"""

from shared.db import SessionSync
from shared.enums import ResourceRolesEnum
from shared.models import ResourceRole
from shared.utils.logger import get_logger

logger = get_logger("seed/resource_roles")


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        for role_enum in ResourceRolesEnum:
            exists = session.query(ResourceRole).filter_by(code=role_enum.code).first()
            if exists:
                logger.info(f"ResourceRole '{role_enum.code}' already exists")
                skipped_count += 1
                continue

            session.add(
                ResourceRole(
                    code=role_enum.code,
                    label=role_enum.label,
                    description=role_enum.description,
                )
            )
            logger.info(f"ResourceRole '{role_enum.code}' added to table")
            added_count += 1
        session.commit()
    logger.info(f"Seed complete: {added_count} added, {skipped_count} skipped.")
