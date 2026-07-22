from uuid import UUID

from shared.db import BaseRepository
from shared.models import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class UserRepository(BaseRepository[User]):
    async def get_by_id(self, id: UUID) -> User | None:
        stmt = select(User).where(User.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def compile_permission_map(self, user_id: UUID) -> dict[str, str]:
        """
        Queries the user and links, fllisto el attening them into a clean string mapping.
        Keeps low-level loop mapping hidden away inside the repository.
        """
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.tier),
            )
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return {}

        permission_map: dict[str, str] = {
            "user_id": str(user.id),
            "is_active": str(user.is_active).lower(),
        }

        # 1. ABAC Attributes (Tier Limits)
        if user.tier:
            permission_map.update(
                {
                    "tier": str(user.tier.label),
                    "max_file_size": str(user.tier.max_file_size),
                    "storage_quota": str(user.tier.storage_quota),
                    "max_requests_per_minute": str(user.tier.max_requests_per_minute),
                    "priority_level": str(user.tier.priority_level),
                }
            )


        return permission_map
