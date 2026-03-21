"""Poblado de user tiers"""

from datetime import datetime, timezone

from shared_db import SessionSync
from shared_models import UserTier
from shared_utils.logger import get_logger

from models import UserTiersEnum as Types

logger = get_logger("seed/user_tiers")


def upgrade() -> None:
    with SessionSync() as session:
        for tier in Types:
            exists = session.query(UserTier).filter_by(label=tier.label).first()
            if exists:
                logger.info(f"{type} already exists in UserTier")
                continue  # Skip this one
            session.add(
                UserTier(
                    label=tier.label,
                    max_file_size=tier.max_file_size,
                    storage_quota=tier.storage_quota,
                    max_requests_per_minute=tier.max_requests_per_minute,
                    priority_level=tier.priority_level,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            logger.info(f"{type} added to table UserTier") 
        session.commit()
