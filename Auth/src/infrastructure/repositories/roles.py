from shared_models import Role
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_label(self, label: str) -> Role | None:
        stmt = select(Role).where(Role.label == label)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default(self) -> Role:
        role = await self.get_by_label("OBSERVER")
        if not role:
            raise ValueError("Default role not found")
        return role
