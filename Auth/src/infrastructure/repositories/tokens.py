from typing import cast

from shared_models import RefreshSession
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_refresh_token_by_jti(
        self, user_id: str, jti: str
    ) -> RefreshSession | None:
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

    async def deactivate_refresh_token(self, user_id: str, jti: str) -> None:
        """
        Marks a token as inactive. Better than deleting if you want to track 'revoked' tokens for security audits.
        """
        stmt = (
            update(RefreshSession)
            .where(
                RefreshSession.user_id == user_id,
                RefreshSession.jti == jti)
            .values(is_active=False)
        )
        await self.session.execute(stmt)

    def create_refresh_token(self, entry: RefreshSession) -> None:
        session = cast(Session, self.session)
        session.add(entry)

    def delete_refresh_token(self, entry: RefreshSession) -> None:
        session = cast(Session, self.session)
        session.delete(entry)
