"""Poblado de users"""

import os
import tomllib
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from shared_db import SessionSync
from shared_models import User, UserTier
from shared_utils import hash_password, sanitize_text
from shared_utils.logger import get_logger
from uuid_utils import uuid7

logger = get_logger("seed/users")


USERS_FILE = "/run/secrets/users_file"
if not os.path.exists(USERS_FILE):
    raise FileNotFoundError(f"USERS_FILE file not found at {USERS_FILE}")
with open(USERS_FILE, "rb") as f:
    users_toml = tomllib.load(f)


def upgrade() -> None:
    with SessionSync() as session:
        # 1. Fetch all tiers in a single query instead of 5 separate ones
        tiers: list[UserTier] = session.query(UserTier).all()
        tier_map = {t.label.lower(): t.id for t in tiers}

        required_labels = {"root", "admin", "premium", "standard", "guest"}
        if not required_labels.issubset(tier_map.keys()):
            missing = required_labels - tier_map.keys()
            logger.error(f"Missing tiers in DB: {missing}")
            raise RuntimeError(f"Required tiers missing: {missing}")

        # 2. Pre-fetch existing emails to avoid "N+1" query problem
        incoming_emails = [u["email"] for u in users_toml.get("users", [])]
        existing_emails = {
            email
            for (email,) in session.query(User.email)
            .filter(User.email.in_(incoming_emails))
            .all()
        }

        # 3. Batch build user objects
        for u in users_toml.get("users", []):
            email = u["email"]
            username = u["username"]

            if email in existing_emails:
                logger.info(f"User {username} already exists, skipping")
                continue

            # Map username to tier, defaulting to admin if no match
            # (Matches your logic where specific usernames might dictate roles)
            tier_id = tier_map.get(username.lower(), tier_map["admin"])

            user_obj = User(
                id=str(uuid7()),
                tier_id=str(tier_id),
                username=username,
                email=email,
                password_hash=hash_password(sanitize_text(u["password"])),
                is_active=True,
                is_verified=True,
                updated_at=datetime.now(timezone.utc),
                media_usage=Decimal("0"),
            )
            session.add(user_obj)
            logger.info(f"Queued user: {username}")

        # 4. Single commit for the entire batch
        session.commit()
