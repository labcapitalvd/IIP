class FileError(Exception):
    """Base error for file utilities and filesystem operations."""


class FileNameError(FileError):
    """Bad, empty, or path-traversal filename."""


class FileExtensionError(FileError):
    """Missing, unsupported, or invalid file extension."""


class FileOSError(FileError):
    """Underlying filesystem or operating system I/O error."""


