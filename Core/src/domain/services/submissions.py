from uuid import UUID
from datetime import datetime, timezone

from shared_models import RefreshSession
from shared_utils.tokens import generate_token, decode_token
from shared_utils.hashing import hash_token, verify_token

from infrastructure.uow import SubmissionUoW

from shared_utils import get_logger
from .errors import TokenRevoked, TokenExpired, TokenError


logger = get_logger(__name__)


class SubmissionService:
    async def example(
        self, user_id: UUID, username: str, uow: SubmissionUoW
    ) -> tuple[str, str]:
        """Generate access and refresh tokens"""
        client_access_token, _, _ = generate_token(
            user_id=user_id, username=username, token_type="access"
        )
        client_refresh_token, expr, jti = generate_token(
            user_id=user_id, username=username, token_type="refresh"
        )

        refresh_hash = hash_token(token=client_refresh_token)

        db_token = RefreshSession(
            jti=jti,
            user_id=user_id,
            refresh_hash=refresh_hash,
            expires_at=datetime.fromtimestamp(expr, tz=timezone.utc),
        )

        uow.tokens.create_refresh_token(entry=db_token)
        return client_access_token, client_refresh_token


