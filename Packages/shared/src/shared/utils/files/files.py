from pathlib import Path
import os
import shutil
import aiofiles
from fastapi import UploadFile

from shared_utils.logger import get_logger

from .errors import FileError, FileNameError, FileOSError

logger = get_logger(__name__)


def _safe_path(base: str, filename: str) -> Path:
    if not filename:
        raise FileNameError("Filename must not be empty.")

    base_path = Path(base).resolve()
    target = (base_path / filename).resolve()

    if not str(target).startswith(str(base_path)):
        raise FileNameError("Invalid filename.")

    return target


async def save_file(
    file: UploadFile,
    filename: str,
    directory: str,
) -> Path:
    os.makedirs(directory, exist_ok=True)
    file_path = _safe_path(directory, filename)
    temp_path = file_path.with_suffix(file_path.suffix + ".part")

    try:
        async with aiofiles.open(temp_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                await f.write(chunk)
            await f.flush()

        os.replace(temp_path, file_path)
        return file_path

    except OSError as e:
        logger.exception("Filesystem error while saving file")
        raise FileOSError("Filesystem error") from e

    except Exception as e:
        logger.exception("Unexpected error while saving file")
        raise FileError("Unexpected error while saving file") from e


def rename_file(old: str, new: str, directory: str) -> Path:
    old_path = _safe_path(directory, old)
    new_path = _safe_path(directory, new)

    try:
        shutil.move(old_path, new_path)
        return new_path
    except OSError as e:
        logger.exception("Filesystem error while renaming file")
        raise FileOSError("Filesystem error") from e


def delete_file(filename: str, directory: str) -> None:
    file_path = _safe_path(directory, filename)

    try:
        if file_path.exists():
            file_path.unlink()
        else:
            raise FileError("File not found.")
    except OSError as e:
        logger.exception("Filesystem error while deleting file")
        raise FileOSError("Filesystem error") from e
