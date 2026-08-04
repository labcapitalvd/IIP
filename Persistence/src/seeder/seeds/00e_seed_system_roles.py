"""Poblado de roles globales (SystemRole) y niveles de acceso (ResourceRole)"""

from shared.db import SessionSync
from shared.enums import ResourceRolesEnum, SystemRolesEnum
from shared.models import ResourceRole, SystemRole
from shared.utils.logger import get_logger

logger = get_logger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    with SessionSync() as session:
        # =====================================================================
        # 1. Poblado de ResourceRole (ReBAC: owner, editor, evaluator, etc.)
        # =====================================================================
        for level_enum in ResourceRolesEnum:
            exists = session.query(ResourceRole).filter_by(code=level_enum.code).first()
            if exists:
                logger.debug(f"ResourceRole '{level_enum.code}' already exists")
                skipped_count += 1
                continue

            session.add(
                ResourceRole(
                    code=level_enum.code,
                    label=level_enum.label,
                    description=level_enum.description,
                )
            )
            logger.debug(f"ResourceRole '{level_enum.code}' added to table")

        # =====================================================================
        # 2. Poblado de SystemRole (RBAC Global: admin, grader, etc.)
        # =====================================================================
        for role_enum in SystemRolesEnum:
            exists = session.query(SystemRole).filter_by(code=role_enum.code).first()
            if exists:
                logger.debug(f"SystemRole '{role_enum.code}' already exists")
                continue

            session.add(
                SystemRole(
                    code=role_enum.code,
                    label=role_enum.label,
                    description=role_enum.description,
                )
            )
            logger.debug(f"SystemRole '{role_enum.code}' added to table")
            added_count += 1
        session.commit()
    logger.debug(f"Seed complete: {added_count} added, {skipped_count} skipped.")
