"""Poblado de user tiers"""

from shared.db import SessionSync
from shared.enums import UserTiersEnum as Types
from shared.models import UserTier
from shared.utils.logger import get_logger

logger = get_logger("seed/user_tiers")


def upgrade() -> None:
    with SessionSync() as session:
        for tier in Types:
            exists: UserTier | None = (
                session.query(UserTier).filter_by(code=tier.code).first()
            )
            if exists:
                logger.info(msg=f"UserTier '{tier.code}' already exists")
                continue  # Skip this one

            session.add(
                UserTier(
                    code=tier.code,
                    label=tier.label,
                    max_file_size=tier.max_file_size,
                    storage_quota=tier.storage_quota,
                    max_requests_per_minute=tier.max_requests_per_minute,
                    priority_level=tier.priority_level,
                )
            )
            logger.info(f"UserTier '{tier.code}' added to table")

        session.commit()
