from typing import Annotated

from fastapi import APIRouter, Depends, Query, Body, Path, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

# from handlers.files import FileHandler
# from schemas.files import (
#     ResponseFiles,
# )
# from utils.allowed_types import FileTypeEnum

# from shared_db import get_session
# from shared_schemas import ResponseMessage
# from shared_utils.tokens import TokenContext

router = APIRouter(tags=["Archivos"], prefix="/files")


# @router.get(
#     "/get/one",
#     response_class=FileResponse,
#     operation_id="get_one_file",
# )
# async def get_media(
#     query: Annotated[RequestFile, Query()],
#     ctx: TokenContext = Depends(),
#     db: AsyncSession = Depends(get_session),
# ):
#     """Function that gets a single file"""
#     current_user = await ctx.get_current_user()
#     return await FileHandler(db, current_user).FileRead(query.id)


# @router.get(
#     "/get/all",
#     response_model=ResponseFiles,
#     response_model_exclude_none=True,
#     operation_id="get_all_files",
# )
# async def get_all_media(
#     ctx: TokenContext = Depends(),
#     db: AsyncSession = Depends(get_session),
# ):
#     """Function that gets all of a users files"""
#     current_user = await ctx.get_current_user()
#     return await FileHandler(db, current_user).FileReadAll()


# @router.post(
#     "/upload",
#     response_model=ResponseMessage,
#     response_model_exclude_none=True,
#     operation_id="upload_file",
# )
# async def upload(
#     file: UploadFile = File(..., description="Archivo a subir"),
#     ctx: TokenContext = Depends(),
#     db: AsyncSession = Depends(get_session),
# ):
#     """Function that uploads a file"""
#     current_user = await ctx.get_current_user()

#     allowed_types = [FileTypeEnum.PNG, FileTypeEnum.JPEG]
#     return await FileHandler(db, current_user).FileCreate(file, allowed_types)


# @router.put(
#     "/edit",
#     response_model=ResponseFile,
#     response_model_exclude_none=True,
#     operation_id="replace_file",
# )
# async def edit_media(
#     form: Annotated[RequestEditFile, Body()],
#     ctx: TokenContext = Depends(),
#     db: AsyncSession = Depends(get_session),
# ):
#     """Function to edit a file."""
#     current_user = await ctx.get_current_user()
#     return await FileHandler(db, current_user).FileRename(form.id, form.filename)


# @router.delete(
#     "/delete/{id}",
#     response_model=ResponseMessage,
#     response_model_exclude_none=True,
#     operation_id="delete_file",
# )
# async def delete_media(
#     path: Annotated[RequestDeleteFile, Path()],
#     ctx: TokenContext = Depends(),
#     db: AsyncSession = Depends(get_session),
# ):
#     """Function to delete a file."""
#     current_user = await ctx.get_current_user()
#     return await FileHandler(db, current_user).FileDelete(path.id)
