import re
import os
from typing import Optional
from uuid import UUID
import hashlib

from fastapi import UploadFile
import unicodedata
from decimal import Decimal

from .allowed_types import FileTypeEnum

class FileError(Exception):
    """Base error for FileUtils."""

class FileNameError(FileError):
    pass

class FileExtensionError(FileError):
    pass


class FileUtils:
    def check_file_type(
        self, filetype: str, allowed_types: list[FileTypeEnum]
    ) -> FileTypeEnum:
        if not filetype:
            raise FileExtensionError("File has no extension.")

        for t in allowed_types:
            if filetype == t.label:
                return t

        raise FileExtensionError("Unsupported file format.")

    def determine_subpath(self, filetype: FileTypeEnum) -> str:
        if not hasattr(filetype, "category"):
            raise FileExtensionError("Invalid file format.")
        return filetype.category

    def sanitize_filename(self, filename: str, extension: Optional[str] = None) -> str:
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

    def generate_file_hash(self, file: UploadFile) -> tuple[str, Decimal]:
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
        except Exception as e:
            raise FileError(f"Exception occurred during hash generation: {e}")
