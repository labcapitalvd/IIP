"""Poblado de user tiers"""

from shared.db import SessionSync
from shared.enums import UserTiersEnum as Types
from shared.models import UserTier
from shared.utils.logger import get_logger

logger = get_logger("seed/user_tiers")


def upgrade() -> None:
    with SessionSync() as session:
        # Load existing tiers keyed by their unique programmatic 'code'
        existing_tiers = {t.code: t for t in session.query(UserTier).all()}

        for tier in Types:
            if tier.code in existing_tiers:
                # Optional: Sync updated quota properties from Enum to DB
                db_tier = existing_tiers[tier.code]
                db_tier.label = tier.label
                db_tier.max_file_size = tier.max_file_size
                db_tier.storage_quota = tier.storage_quota
                db_tier.max_requests_per_minute = tier.max_requests_per_minute
                db_tier.priority_level = tier.priority_level
                logger.info(f"UserTier '{tier.code}' updated")
            else:
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
                logger.info(f"UserTier '{tier.code}' inserted")

        session.commit()
