"""Poblado de user tiers"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from shared_db import SessionSync
from shared_models import UserTier
from shared_utils.logging import get_logger


logger = get_logger("seed/user_tiers")


class Types(Enum):
    ROOT = (Decimal(500 * 1024 * 1024), Decimal(100 * 1024 * 1024 * 1024), 500, 5)
    ADMIN = (Decimal(100 * 1024 * 1024), Decimal(50 * 1024 * 1024 * 1024), 300, 4)
    PREMIUM = (Decimal(50 * 1024 * 1024), Decimal(20 * 1024 * 1024 * 1024), 120, 3)
    STANDARD = (Decimal(10 * 1024 * 1024), Decimal(10 * 1024 * 1024 * 1024), 60, 2)
    GUEST = (Decimal(5 * 1024 * 1024), Decimal(5 * 1024 * 1024 * 1024), 30, 1)

    def __init__(
        self, max_file_size, storage_quota, max_requests_per_minute, priority_level
    ):
        self.max_file_size = max_file_size
        self.storage_quota = storage_quota
        self.max_requests_per_minute = max_requests_per_minute
        self.priority_level = priority_level

    @property
    def label(self):
        return self.name  # Use the enum member name itself


def upgrade() -> None:
    with SessionSync() as session:
        for tier in Types:
            exists = session.query(UserTier).filter_by(label=tier.label).first()
            if exists:
                continue  # Skip this one
            session.add(
                UserTier(
                    label=tier,
                    max_file_size=tier.max_file_size,
                    storage_quota=tier.storage_quota,
                    max_requests_per_minute=tier.max_requests_per_minute,
                    priority_level=tier.priority_level,
                    updated_at=datetime.now(timezone.utc),
                )
            )
        session.commit()
