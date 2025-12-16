from uuid import UUID
import os
from typing import List

from fastapi import UploadFile
from fastapi.responses import FileResponse

from sqlalchemy.ext.asyncio import AsyncSession

from db.files import FileDb
from utils.files import FileUtils
from schemas.files import ResponseFile
from utils.allowed_types import FileTypeEnum

from shared_schemas import ItemError, CustomError
from shared_schemas import ResponseMessage
from shared_utils import TextUtils, FileDisk

BASE_UPLOAD_DIR = os.environ["BASE_UPLOAD_DIR"]
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)


class FileHandler:
    def __init__(self, db: AsyncSession, current_user: UUID):
        self.db = db
        self.basepath = BASE_UPLOAD_DIR
        self.user = current_user

        self.fileutils = FileUtils()
        self.textutils = TextUtils()
        self.fileondb = FileDb(self.db)
        self.fileondisk = FileDisk()

    async def FileCreate(
        self, file: UploadFile, allowed_types: List[FileTypeEnum]
    ) -> ResponseFile:
        if not file.filename or not file.content_type:
            raise CustomError(
                errors=[
                    ItemError(
                        code="INVALID_FILE",
                        message="Invalid file",
                        more_info="File must have a name and content type",
                    )
                ]
            )

        filetype = self.fileutils.check_file_type(file.content_type, allowed_types)
        ft = await self.fileondb.get_filetype(filetype)
        subpath = self.fileutils.determine_subpath(filetype)
        filename = self.fileutils.sanitize_filename(
            file.filename, extension=filetype.extension
        )
        filehash, filesize = self.fileutils.generate_file_hash(file)

        filepath = os.path.join(self.basepath, str(self.user.id), subpath)

        existing_file = await self.fileondb.check_duplicity(self.user.id, filehash)
        if existing_file:
            await self.fileondisk.rename_file(
                user_id=self.user.id,
                old_filename=existing_file.filename,
                new_filename=filename,
                filepath=existing_file.filepath,
            )
            await self.fileondb.update_file_entry(
                id=existing_file.id, owner=self.user.id, filename=filename
            )
            return ResponseFile(id=existing_file.id)

        media = await self.fileondb.create_file_entry(
            owner=self.user.id,
            file_type_id=ft.id,
            filename=filename,
            filepath=filepath,
            filehash=filehash,
            filesize=filesize,
        )
        file.file.seek(0)
        await self.fileondisk.save_file(self.user.id, file, filename, media.filepath)
        return ResponseFile(id=media.id)

    async def FileRename(self, id: UUID, new_filename: str) -> ResponseFile:
        filename = self.fileutils.sanitize_filename(new_filename)
        media = await self.fileondb.get_file_entry(id=id, owner=self.user.id)

        if media.filename == filename:
            return ResponseFile(id=media.id)

        await self.fileondisk.rename_file(
            user_id=self.user.id,
            old_filename=media.filename,
            new_filename=filename,
            filepath=media.filepath,
        )
        updated_media = await self.fileondb.update_file_entry(
            id=media.id, owner=self.user.id, filename=filename
        )
        return ResponseFile(id=updated_media.id)

    async def FileRead(self, id: UUID) -> FileResponse:
        media = await self.fileondb.get_file_entry(id=id, owner=self.user.id)
        return FileResponse(
            path=f"{media.filepath}/{media.filename}",
            media_type=media.type.mime_type,
            filename=media.filename,
        )

    async def FileReadAll(self) -> List[ResponseFile]:
        mediaqueries = await self.fileondb.get_all_file_entries(owner=self.user.id)
        medias = []
        for i in mediaqueries:
            medias.append(ResponseFile(id=i.id))
        return medias

    async def FileDelete(self, id: UUID) -> ResponseMessage:
        media = await self.fileondb.get_file_entry(id=id, owner=self.user.id)
        filepath = media.filepath
        filename = media.filename

        await self.fileondb.delete_file_entry(id=id, owner=self.user.id)
        await self.fileondisk.delete_file(self.user.id, filename, filepath)
        return ResponseMessage(message="Archivo eliminado correctamente")
