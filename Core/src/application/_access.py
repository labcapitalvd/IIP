from uuid import UUID

from sqlalchemy import select

from shared.enums import SystemRolesEnum
from shared.models import UserSystemRoleLink


async def is_admin(session, user_id: UUID) -> bool:
    """True si el usuario tiene el rol de sistema de administrador de la plataforma."""
    found = await session.scalar(
        select(UserSystemRoleLink.id)
        .join(UserSystemRoleLink.system_role)
        .where(
            UserSystemRoleLink.user_id == user_id,
            UserSystemRoleLink.system_role.has(code=SystemRolesEnum.PLATFORM_ADMIN.code),
        )
    )
    return found is not None
