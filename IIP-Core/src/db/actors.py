from uuid import UUID
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from shared_schemas import CustomError, ItemError
from models import Actor


class ActorDb:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_actor_entry(self, id: UUID) -> Actor:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(Actor)
                .options(selectinload(Actor.actor_segment))
                .where(
                    Actor.id == id,
                )
            )
            return result.scalar_one()

        except NoResultFound:
            raise CustomError(
                errors=[
                    ItemError(
                        code="ENTITY_NOT_FOUND",
                        message="Actor not found",
                        more_info=f"No actor exists with id: {id}",
                    )
                ]
            )

        except Exception as e:
            raise CustomError(
                errors=[
                    ItemError(
                        code="EXCEPTION_ON_GET_ENTITY_ENTRY",
                        message="Error fetching actor entry.",
                        more_info=str(e),
                    )
                ]
            )

    async def get_all_actor_entries(self) -> Sequence[Actor]:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(Actor)
                .options(selectinload(Actor.actor_segment))
            )
            return result.scalars().all()

        except Exception as e:
            raise CustomError(
                errors=[
                    ItemError(
                        code="EXCEPTION_ON_GET_ENTITY_ENTRIES",
                        message="Error getting actor entries.",
                        more_info=str(e),
                    )
                ]
            )
