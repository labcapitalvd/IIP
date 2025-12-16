from uuid import UUID
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from shared_schemas import CustomError, ItemError
from models import Form


class FormDb:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_form_edition_entry(self, id: UUID) -> Form:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(Form)
                # .options(selectinload(Form.actors))
                .where(
                    Form.id == id,
                )
            )
            return result.scalar_one()

        except NoResultFound:
            raise CustomError(
                errors=[
                    ItemError(
                        code="INDEX_EDITION_NOT_FOUND",
                        message="Form edition not found",
                        more_info=f"No form edition exists with id: {id}",
                    )
                ]
            )

        except Exception as e:
            raise CustomError(
                errors=[
                    ItemError(
                        code="EXCEPTION_ON_GET_INDEX_EDITION_ENTRY",
                        message="Error fetching form edition entry.",
                        more_info=str(e),
                    )
                ]
            )

    async def get_all_form_edition_entries(self) -> Sequence[Form]:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(Form)
            )
            return result.scalars().all()

        except Exception as e:
            raise CustomError(
                errors=[
                    ItemError(
                        code="EXCEPTION_ON_GET_INDEX_EDITION_ENTRIES",
                        message="Error getting form edition entries.",
                        more_info=str(e),
                    )
                ]
            )
