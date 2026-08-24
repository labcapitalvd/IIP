from uuid import UUID
from shared.db import BaseRepository
from shared.models import RefreshSession
from sqlalchemy import select, update


class RefreshTokenRepository(BaseRepository[RefreshSession]):
    model = RefreshSession

    @staticmethod
    def _to_uuid(val: UUID | str) -> UUID:
        return UUID(val) if isinstance(val, str) else val

    async def get_by_jti(
        self, user_id: UUID | str, jti: UUID | str
    ) -> RefreshSession | None:
        """
        Gets a token from the db with JTI and checks if ownership
        corresponds to user.
        """
        stmt = select(RefreshSession).where(
            RefreshSession.user_id == self._to_uuid(user_id),
            RefreshSession.jti == self._to_uuid(jti),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, user_id: UUID | str, jti: UUID | str) -> None:
        """
        Marks a token as inactive. Better than deleting if you want to track 'revoked' tokens for security audits.
        """
        stmt = (
            update(RefreshSession)
            .where(
                RefreshSession.user_id == self._to_uuid(user_id),
                RefreshSession.jti == self._to_uuid(jti),
            )
            .values(is_active=False)
        )
        await self.session.execute(stmt)
