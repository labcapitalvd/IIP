"""Poblado de roles globales (SystemRole) y niveles de acceso (AccessLevel)"""

from shared.db import SessionSync
from shared.enums import AccessLevelsEnum, SystemRolesEnum
from shared.models import AccessLevel, SystemRole
from shared.utils.logger import get_logger

logger = get_logger("seed/security_roles")


def upgrade() -> None:
    with SessionSync() as session:
        # =====================================================================
        # 1. Poblado de AccessLevel (ReBAC: owner, editor, evaluator, etc.)
        # =====================================================================
        for level_enum in AccessLevelsEnum:
            exists = session.query(AccessLevel).filter_by(code=level_enum.code).first()
            if exists:
                logger.info(f"AccessLevel '{level_enum.code}' already exists")
                continue

            session.add(
                AccessLevel(
                    code=level_enum.code,
                    label=level_enum.label,
                    description=level_enum.description,
                )
            )
            logger.info(f"AccessLevel '{level_enum.code}' added to table")

        # =====================================================================
        # 2. Poblado de SystemRole (RBAC Global: admin, grader, etc.)
        # =====================================================================
        for role_enum in SystemRolesEnum:
            exists = session.query(SystemRole).filter_by(code=role_enum.code).first()
            if exists:
                logger.info(f"SystemRole '{role_enum.code}' already exists")
                continue

            session.add(
                SystemRole(
                    code=role_enum.code,
                    label=role_enum.label,
                    description=role_enum.description,
                )
            )
            logger.info(f"SystemRole '{role_enum.code}' added to table")

        session.commit()
