import os
from uuid import UUID
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

import logging

from shared_utils import HashUtils
from shared_models import User, UserTier

LOGLEVEL = os.environ["LOGLEVEL"].lower() in (
    "debug",
    "info",
    "warning",
    "error",
    "critical",
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_HASHER_PASS = os.environ["JWT_HASHER_PASS"]

logger = logging.getLogger("api/db")
logger.setLevel(LOGLEVEL)


class UsersDb:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_entry(
        self,
        id: Optional[UUID] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Optional[User]:
        """Fetch a User by ID, username, or email."""
        try:
            if id:
                stmt = select(User).where(User.id == id)
            elif username:
                stmt = select(User).where(User.username == username)
            elif email:
                stmt = select(User).where(User.email == email)
            else:
                raise ValueError("Must supply id, username, or email")
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                return user

            return None

        except Exception as e:
            logger.error(f"Unknown error: {e}")
            raise

    async def create_user_entry(
        self, username: str, email: str, passwd: str
    ) -> Optional[User]:
        """Create an entry in the database for the user"""

        try:
            tier = (
                await self.db.execute(
                    select(UserTier).where(UserTier.label == "STANDARD")
                )
            ).scalar_one_or_none()

            if not tier:
                raise ValueError("Default user tier not found")

            user = User(
                username=username,
                email=email,
                password_hash=HashUtils.hash_string(passwd),
                is_active=True,
                tier_id=tier.id,
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error: {e}")
            raise

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unknown error: {e}")
            raise

    async def update_user_entry(
        self,
        *,
        id: UUID,
        new_username: Optional[str] = None,
        new_email: Optional[str] = None,
        new_password: Optional[str] = None,
    ) -> Optional[User]:
        "Update a user's fields dynamically."
        try:
            user = (
                await self.db.execute(select(User).where(User.id == id))
            ).scalar_one_or_none()

            if not user:
                return None

            if new_username is not None:
                user.username = new_username
            if new_email is not None:
                user.email = new_email
            if new_password is not None:
                user.password_hash = HashUtils.hash_string(new_password)

            await self.db.commit()
            await self.db.refresh(user)
            return user

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"IntegrityError: {e}")
            raise

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unknown error: {e}")
            raise

    async def delete_user_entry(
        self, passwd: str, username: Optional[str] = None, email: Optional[str] = None
    ) -> bool:
        "Delete a user by username/email and password."
        try:
            if not username and not email:
                raise ValueError("Must supply username or email")

            result = await self.db.execute(
                select(User).where(or_(User.username == username, User.email == email))
            )
            user = result.scalar_one_or_none()
            if not user:
                return False

            # Check password
            if not HashUtils.verify_hash(passwd, user.password_hash):
                return False

            # Delete
            await self.db.delete(user)
            await self.db.commit()
            return True

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"IntegrityError: {e}")
            raise

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unknown error: {e}")
            raise
