from uuid import UUID
from datetime import datetime, timezone
from typing import Sequence, Optional
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError

from utils.allowed_types import FileTypeEnum

from shared_models import File, FileType


class FileDb:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_filetype(self, filetypeenum: FileTypeEnum) -> FileType:
        """Check if a file with the given hash exists for the owner"""
        try:
            result = await self.db.execute(
                select(FileType).where(FileType.label == filetypeenum.label)
            )
            return result.scalar_one()
        except Exception as e:
            raise 

    async def check_duplicity(self, owner: UUID, filehash: str) -> Optional[File]:
        """Check if a file with the given hash exists for the owner"""
        try:
            result = await self.db.execute(
                select(File).where(File.filehash == filehash, File.user_id == owner)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise 

    async def get_file_entry(self, id: UUID, owner: UUID) -> File:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(File).where(
                    File.id == id,
                    File.user_id == owner,
                )
            )
            return result.scalar_one()

        except NoResultFound:
            raise 

        except Exception as e:
            raise 

    async def get_all_file_entries(self, owner: UUID) -> Sequence[File]:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(File).where(
                    File.user_id == owner,
                )
            )
            return result.scalars().all()

        except Exception as e:
            raise 

    async def create_file_entry(
        self,
        owner: UUID,
        file_type_id: UUID,
        filename: str,
        filepath: str,
        filehash: str,
        filesize: Decimal,
    ) -> File:
        """Create an entry in the database for the uploaded file"""
        try:
            media = File(
                user_id=owner,
                file_type_id=file_type_id,
                created_at=datetime.now(timezone.utc),
                filename=filename,
                filepath=filepath,
                filehash=filehash,
                filesize=filesize,
            )

            self.db.add(media)
            await self.db.commit()
            await self.db.refresh(media)
            return media
        except Exception as e:
            await self.db.rollback()
            raise 

    async def update_file_entry(
        self,
        id: UUID,
        owner: UUID,
        filetype_id: Optional[UUID] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        filehash: Optional[str] = None,
    ) -> File:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(File).where(
                    File.id == id,
                    File.user_id == owner,
                )
            )
            media = result.scalar_one()

            if filetype_id is not None:
                media.file_type_id = filetype_id
            if filename is not None:
                media.filename = filename
            if filehash is not None:
                media.filehash = filehash
            if filepath is not None:
                media.filepath = filepath

            await self.db.commit()
            await self.db.refresh(media)
            return media

        except NoResultFound:
            raise 

        except IntegrityError as e:
            await self.db.rollback()
            raise 

        except Exception as e:
            await self.db.rollback()
            raise 

    async def delete_file_entry(self, id: UUID, owner: UUID) -> None:
        """Create an entry in the database for the uploaded file"""
        try:
            result = await self.db.execute(
                select(File).where(
                    File.id == id,
                    File.user_id == owner,
                )
            )
            media = result.scalar_one()

            await self.db.delete(media)
            await self.db.commit()

        except NoResultFound:
            raise 

        except IntegrityError as e:
            await self.db.rollback()
            raise 

        except Exception as e:
            await self.db.rollback()
            raise 