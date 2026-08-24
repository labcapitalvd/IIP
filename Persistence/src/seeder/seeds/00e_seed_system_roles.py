"""Poblado de roles globales (SystemRole) y niveles de acceso (ResourceRole)"""

from shared.db import SessionSync
from shared.enums import SystemRolesEnum
from shared.models import SystemRole
from shared.utils.logger import getLogger
from sqlalchemy import select

logger = getLogger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch existing codes for both tables in 2 single queries
        existing_system_roles = set(session.scalars(select(SystemRole.code)).all())

        new_system_roles: list[SystemRole] = []
        # =====================================================================
        # 2. Poblado de SystemRole (RBAC Global: admin, grader, etc.)
        # =====================================================================
        for role_enum in SystemRolesEnum:
            if role_enum.code in existing_system_roles:
                logger.debug(f"SystemRole '{role_enum.code}' already exists")
                skipped_count += 1
                continue

            new_system_roles.append(
                SystemRole(
                    code=role_enum.code,
                    label=role_enum.label,
                    description=role_enum.description,
                )
            )
            logger.debug(f"Queued '{role_enum.code}' for SystemRole")
            added_count += 1

        if new_system_roles:
            session.add_all(new_system_roles)
            session.commit()

    logger.debug(f"Roles seed complete: {added_count} added, {skipped_count} skipped.")
