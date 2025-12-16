from uuid import UUID
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from shared_schemas import CustomError, ItemError
from models import ActorSegment


class ActorSegmentDb:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_actor_segment_entry(self, id: UUID) -> ActorSegment:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(ActorSegment)
                .options(selectinload(ActorSegment.actors))
                .where(
                    ActorSegment.id == id,
                )
            )
            return result.scalar_one()

        except NoResultFound:
            raise CustomError(
                errors=[
                    ItemError(
                        code="SECTOR_NOT_FOUND",
                        message="ActorSegment not found",
                        more_info=f"No actor_segment exists with id: {id}",
                    )
                ]
            )

        except Exception as e:
            raise CustomError(
                errors=[
                    ItemError(
                        code="EXCEPTION_ON_GET_SECTOR_ENTRY",
                        message="Error fetching actor_segment entry.",
                        more_info=str(e),
                    )
                ]
            )

    async def get_all_actor_segment_entries(self) -> Sequence[ActorSegment]:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(ActorSegment)
                .options(selectinload(ActorSegment.actors)) 
            )
            return result.scalars().all()

        except Exception as e:
            raise CustomError(
                errors=[
                    ItemError(
                        code="EXCEPTION_ON_GET_SECTOR_ENTRIES",
                        message="Error getting actor_segment entries.",
                        more_info=str(e),
                    )
                ]
            )
