from typing import Sequence
from uuid import UUID

from shared.db import BaseRepository
from shared.enums import FileTypesEnum
from shared.models import Attachment, File, FileType
from sqlalchemy import select


class FileRepository(BaseRepository[File]):
    """Repository for File, FileType, and Attachment entities."""

    model = File

    # --- FileType Lookups ---

    async def get_filetype(self, filetype_enum: FileTypesEnum) -> FileType | None:
        """Fetch FileType metadata record by enum value/label."""
        stmt = select(FileType).where(FileType.label == filetype_enum.value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- File Lookups ---

    async def get_by_id_and_owner(self, id: UUID, owner_id: UUID) -> File | None:
        """Fetch file by ID ensuring owner matching."""
        stmt = select(File).where(File.id == id, File.uploaded_by_user_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_filename(self, filename: str, owner_id: UUID) -> File | None:
        """Fetch file record by filename for a specific user."""
        stmt = select(File).where(
            File.filename == filename, File.uploaded_by_user_id == owner_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_hash(self, filehash: str) -> File | None:
        """Fetch low-level physical file metadata by content SHA hash (CAS lookups)."""
        stmt = select(File).where(File.filehash == filehash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_owner(self, owner_id: UUID) -> Sequence[File]:
        """Fetch all physical files uploaded by a given user."""
        stmt = select(File).where(File.uploaded_by_user_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # --- Attachment Lookups (Contextual File References) ---

    async def get_attachments_for_entity(
        self, entity_type: str, entity_id: UUID
    ) -> Sequence[Attachment]:
        """Fetch all contextual attachments linked to a domain entity."""
        stmt = select(Attachment).where(
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
