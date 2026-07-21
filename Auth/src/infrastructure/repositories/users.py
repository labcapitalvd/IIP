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

    async def compile_permission_map(self, user_id: str) -> dict[str, str]:
        """
        Queries the user and links, fllisto el attening them into a clean string mapping.
        Keeps low-level loop mapping hidden away inside the repository.
        """
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.file_links),
                selectinload(User.actor_links),
                selectinload(User.submission_links),
            )
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return {}

        permission_map: dict[str, str] = {}

        for link in user.file_links:
            if link.role:
                permission_map[f"file:{link.file_id}"] = str(link.role)

        for link in user.actor_links:
            if link.role:
                permission_map[f"actor:{link.actor_id}"] = str(link.role)

        for link in user.submission_links:
            if link.role:
                permission_map[f"submission:{link.submission_id}"] = str(link.role)

        return permission_map
