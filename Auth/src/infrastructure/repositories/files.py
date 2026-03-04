from typing import Sequence
from uuid import UUID

from shared_models import File, FileType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.allowed_types import FileTypeEnum


class FileRepository:
    """Repository for File and FileType aggregates. No commits/rollbacks here."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_filetype(self, filetype_enum: FileTypeEnum) -> FileType:
        stmt = select(FileType).where(FileType.label == filetype_enum.label)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_file_by_id(self, id: UUID, owner: UUID) -> File | None:
        stmt = select(File).where(File.id == id, File.user_id == owner)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_file_by_filename(self, filename: str, owner: UUID) -> File | None:
        stmt = select(File).where(File.filename == filename, File.user_id == owner)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_file_by_hash(self, filehash: str, owner: UUID) -> File | None:
        stmt = select(File).where(File.filehash == filehash, File.user_id == owner)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_files(self, owner: UUID) -> Sequence[File]:
        stmt = select(File).where(File.user_id == owner)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_file(self, entry: File) -> None:
        self.session.add(entry)

    async def delete_file(self, entry: File) -> None:
        await self.session.delete(entry)
