"""Poblado de user tiers"""

from shared.db import SessionSync
from shared.enums import UserTiersEnum as Types
from shared.models import UserTier
from shared.utils.logger import getLogger
from sqlalchemy import select

logger = getLogger(__name__)


def upgrade() -> None:
    added_count = 0
    updated_count = 0

    with SessionSync() as session:
        # Load existing tiers in 1 single query (SQLAlchemy 2.0 style)
        existing_tiers = {
            tier.code: tier for tier in session.scalars(select(UserTier)).all()
        }

        new_records: list[UserTier] = []

        for tier in Types:
            if tier.code in existing_tiers:
                # Sync updated properties from Enum to existing DB record
                db_tier = existing_tiers[tier.code]
                db_tier.label = tier.label
                db_tier.description = tier.description
                db_tier.max_file_size = tier.max_file_size
                db_tier.storage_quota = tier.storage_quota
                db_tier.max_requests_per_minute = tier.max_requests_per_minute
                db_tier.priority_level = tier.priority_level

                updated_count += 1
                logger.debug(f"UserTier '{tier.code}' updated")
            else:
                new_records.append(
                    UserTier(
                        code=tier.code,
                        label=tier.label,
                        description=tier.description,
                        max_file_size=tier.max_file_size,
                        storage_quota=tier.storage_quota,
                        max_requests_per_minute=tier.max_requests_per_minute,
                        priority_level=tier.priority_level,
                    )
                )
                logger.debug(f"Queued '{tier.code}' for UserTier")
                added_count += 1

        # Bulk insert new records and persist sync updates
        if new_records:
            session.add_all(new_records)

        session.commit()

    logger.debug(
        f"UserTier seed complete: {added_count} added, {updated_count} updated."
    )
