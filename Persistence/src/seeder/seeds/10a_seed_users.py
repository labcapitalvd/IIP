"""Poblado de users"""

import os
import tomllib
from datetime import datetime, timezone
from decimal import Decimal
from uuid_utils import uuid7

from shared_db import SessionSync
from shared_models import User, UserTier
from shared_utils.logger import get_logger
from shared_utils import hash_password, sanitize_text


logger = get_logger("seed/users")


USERS_FILE = "/run/secrets/users_file"
if not os.path.exists(USERS_FILE):
    raise FileNotFoundError(f"USERS_FILE file not found at {USERS_FILE}")
with open(USERS_FILE, "rb") as f:
    users_toml = tomllib.load(f)


def upgrade() -> None:
    with SessionSync() as session:
        root_tier = session.query(UserTier).filter_by(label="ROOT").first()
        admin_tier = session.query(UserTier).filter_by(label="ADMIN").first()
        premium_tier = session.query(UserTier).filter_by(label="PREMIUM").first()
        standard_tier = session.query(UserTier).filter_by(label="STANDARD").first()
        guest_tier = session.query(UserTier).filter_by(label="GUEST").first()
        if not root_tier or not admin_tier:
            logger.error("One tier not found in DB")
            raise RuntimeError("One tier not found in DB")

        tier_map = {
            "root": root_tier.id,
            "admin": admin_tier.id,
            "premium": premium_tier.id,
            "standard": standard_tier.id,
            "guest": guest_tier.id,
        }

        for u in users_toml.get("users", []):
            tier_id = tier_map.get(u["username"].lower(), admin_tier.id)
            exists = session.query(User).filter_by(email=u["email"]).first()
            if exists:
                logger.debug(f"User {u['username']} already exists, skipping")
                continue

            user_obj = User(
                id=uuid7(),
                tier_id=tier_id,
                username=u["username"],
                email=u["email"],
                password_hash=hash_password(sanitize_text(u["password"])),
                is_active=True,
                is_verified=True,
                updated_at=datetime.now(timezone.utc),
                media_usage=Decimal(0),
            )
            session.add(user_obj)
            logger.info(f"Added user {u['username']}")
        session.commit()
