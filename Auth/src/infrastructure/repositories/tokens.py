from uuid import UUID
from shared.db import BaseRepository
from shared.models import RefreshSession
from sqlalchemy import select, update


class RefreshTokenRepository(BaseRepository[RefreshSession]):
    async def get_by_jti(self, user_id: UUID, jti: UUID) -> RefreshSession | None:
        """
        Gets a token from the db with JTI and checks if ownership
        corresponds to user.
        """
        stmt = select(RefreshSession).where(
            RefreshSession.user_id == user_id,
            RefreshSession.jti == jti,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, user_id: UUID, jti: UUID) -> None:
        """
        Marks a token as inactive. Better than deleting if you want to track 'revoked' tokens for security audits.
        """
        stmt = (
            update(RefreshSession)
            .where(RefreshSession.user_id == user_id, RefreshSession.jti == jti)
            .values(is_active=False)
        )
        await self.session.execute(stmt)
