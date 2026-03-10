class FileError(Exception):
    """Base error for FileDisk."""


class FileNameError(FileError):
    """Bad filename or path"""


class FileOSError(FileError):
    """General OS error"""

