import hashlib
import os
import re
import shutil
import unicodedata
from decimal import Decimal
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from shared.enums import FileTypesEnum
from shared.utils.logger import getLogger

from .errors import FileError, FileExtensionError, FileNameError, FileOSError

logger = getLogger(__name__)



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


class FileUtils:
    """
    Unified utility suite for file type inspection, filename sanitization,
    checksum hashing, and storage subpath determination.
    Methods can be called as static methods or through class instances.
    """

    @staticmethod
    def check_file_type(
        filetype: str, allowed_types: list[FileTypesEnum]
    ) -> FileTypesEnum:
        if not filetype:
            raise FileExtensionError("File has no extension.")

        normalized_ft = filetype.strip().lower()
        for t in allowed_types:
            if (
                filetype == t.label
                or normalized_ft == t.label.lower()
                or normalized_ft == t.extension.lower()
                or normalized_ft == t.extension.lstrip(".").lower()
                or normalized_ft == t.code.lower()
            ):
                return t

        raise FileExtensionError("Unsupported file format.")

    @staticmethod
    def determine_subpath(filetype: FileTypesEnum) -> str:
        if not hasattr(filetype, "category"):
            raise FileExtensionError("Invalid file format.")
        return filetype.category

    @staticmethod
    def sanitize_filename(filename: str, extension: str | None = None) -> str:
        # Split into base name + extension
        n, e = os.path.splitext(filename)

        # Normalize case
        name = n.lower()
        ext = e.lower()

        # Use given extension or original one
        if extension is None:
            extension = ext
        else:
            extension = extension.lower()

        # Ensure extension starts with a dot if present
        if extension and not extension.startswith("."):
            extension = "." + extension

        if not name or name.strip() == "":
            raise FileNameError("Empty file name.")

        # Normalize unicode
        name = unicodedata.normalize("NFKC", name)

        # Replace dangerous characters
        name = re.sub(r'[<>:"/\\|?*]', "_", name)  # unsafe chars
        name = re.sub(r"[\x00-\x1f\x7f]", "", name)  # control chars
        name = re.sub(r"[–—]", "-", name)  # normalize fancy dashes

        # Whitespace & underscores
        name = name.replace(" ", "_")
        name = re.sub(r"_+", "_", name)
        name = name.strip(" ._")

        # Windows reserved names (case-insensitive)
        reserved = {
            r.lower()
            for r in (
                {"CON", "PRN", "AUX", "NUL"}
                | {f"COM{i}" for i in range(1, 10)}
                | {f"LPT{i}" for i in range(1, 10)}
            )
        }
        if name in reserved:
            raise FileError("Reserved name.")

        if not name or name in {".", ".."}:
            raise FileNameError("Invalid file name.")

        # Truncate if too long (account for extension)
        max_len = 255 - len(extension)
        if len(name) > max_len:
            name = name[:max_len]

        return f"{name}{extension}"

    @staticmethod
    def generate_file_hash(file: UploadFile) -> tuple[str, Decimal]:
        try:
            hasher = hashlib.sha256()
            total_size = 0
            while chunk := file.file.read(8192):
                hasher.update(chunk)
                total_size += len(chunk)
            file.file.seek(0)

            if total_size == 0:
                raise FileError("Empty file.")

            return hasher.hexdigest(), Decimal(total_size)
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"Exception occurred during hash generation: {e}") from e

    # Expose disk operations through FileUtils as well
    save_file = staticmethod(save_file)
    rename_file = staticmethod(rename_file)
    delete_file = staticmethod(delete_file)

