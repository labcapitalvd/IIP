"""Poblado de users"""

import os
import tomllib
from datetime import datetime, timezone
from decimal import Decimal

from shared.db import SessionSync
from shared.models import User, UserTier
from shared.utils import hash_password
from shared.utils.logger import get_logger
from uuid_utils import uuid7

logger = get_logger(__name__)
USERS_FILE = "/run/secrets/users_file"


def load_users_config() -> dict:
    if not os.path.exists(USERS_FILE):
        raise FileNotFoundError(f"USERS_FILE not found at {USERS_FILE}")
    with open(USERS_FILE, "rb") as f:
        return tomllib.load(f)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0
    users_toml = load_users_config()

    with SessionSync() as session:
        # 1. Fetch tiers and map by t.code (matches UserTiersEnum.code)
        tiers: list[UserTier] = session.query(UserTier).all()
        tier_map = {t.code.lower(): t.id for t in tiers}

        required_codes = {"root", "admin", "premium", "standard", "guest"}
        if not required_codes.issubset(tier_map.keys()):
            missing = required_codes - tier_map.keys()
            logger.error(f"Missing required tier codes in DB: {missing}")
            raise RuntimeError(f"Required tier codes missing: {missing}")

        # 2. Pre-fetch existing emails
        incoming_users = users_toml.get("users", [])
        incoming_emails = [u["email"] for u in incoming_users if "email" in u]

        existing_emails = {
            email
            for (email,) in session.query(User.email)
            .filter(User.email.in_(incoming_emails))
            .all()
        }

        # 3. Batch build users
        for u in incoming_users:
            email = u["email"]
            username = u["username"]

            if email in existing_emails:
                logger.debug(f"User {username} ({email}) already exists, skipping")
                skipped_count += 1
                continue

            # Read target tier from user dictionary (defaults to "standard")
            target_tier_code = u.get("tier", "standard").lower()
            tier_id = tier_map.get(target_tier_code, tier_map["standard"])

            user_obj = User(
                id=str(uuid7()),
                tier_id=str(tier_id),
                username=username,
                email=email,
                password_hash=hash_password(u["password"]),  # Direct raw password
                is_active=True,
                is_verified=True,
                updated_at=datetime.now(timezone.utc),
                media_usage=Decimal("0"),
            )
            session.add(user_obj)
            logger.debug(f"Queued user: {username} [Tier: {target_tier_code}]")
            added_count += 1
        session.commit()
    logger.debug(f"Seed complete: {added_count} added, {skipped_count} skipped.")
