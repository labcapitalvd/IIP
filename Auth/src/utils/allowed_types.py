from decimal import Decimal
from enum import Enum


class FileTypeEnum(Enum):
    EXCEL_1 = ("application/vnd.ms-excel", ".xls", "tabular", Decimal(10 * 1024 * 1024))
    EXCEL_2 = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
        "tabular",
        Decimal(20 * 1024 * 1024),
    )
    OPEN_EXCEL_1 = (
        "application/vnd.oasis.opendocument.spreadsheet",
        ".ods",
        "tabular",
        Decimal(10 * 1024 * 1024),
    )
    OPEN_EXCEL_2 = (
        "application/vnd.oasis.opendocument.spreadsheet",
        ".odf",
        "tabular",
        Decimal(10 * 1024 * 1024),
    )
    CSV = ("text/csv", ".csv", "tabular", Decimal(10 * 1024 * 1024))
    TSV = ("text/tab-separated-values", ".tsv", "tabular", Decimal(10 * 1024 * 1024))

    PNG = ("image/png", ".png", "images", Decimal(10 * 1024 * 1024))
    JPEG = ("image/jpeg", ".jpg", "images", Decimal(5 * 1024 * 1024))
    WEBP = ("image/webp", ".webp", "images", Decimal(5 * 1024 * 1024))
    GIF = ("image/gif", ".gif", "images", Decimal(5 * 1024 * 1024))
    AVIF = ("image/avif", ".avif", "images", Decimal(5 * 1024 * 1024))

    MP4 = ("video/mp4", ".mp4", "videos", Decimal(500 * 1024 * 1024))
    WEBM = ("video/webm", ".webm", "videos", Decimal(500 * 1024 * 1024))
    MOV = ("video/quicktime", ".mov", "videos", Decimal(1 * 1024 * 1024 * 1024))

    PDF = ("application/pdf", ".pdf", "docs", Decimal(50 * 1024 * 1024))
    WORD = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
        "docs",
        Decimal(20 * 1024 * 1024),
    )
    OPEN_WORD = (
        "application/vnd.oasis.opendocument.text",
        ".odt",
        "docs",
        Decimal(20 * 1024 * 1024),
    )
    POWERPOINT = (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
        "docs",
        Decimal(50 * 1024 * 1024),
    )
    OPEN_POWERPOINT = (
        "application/vnd.oasis.opendocument.presentation",
        ".odp",
        "docs",
        Decimal(50 * 1024 * 1024),
    )

    ZIP = ("application/zip", ".zip", "archives", Decimal(200 * 1024 * 1024))
    RAR = ("application/x-rar", ".rar", "archives", Decimal(200 * 1024 * 1024))
    SEVEN_ZIP = (
        "application/x-7z-compressed",
        ".7z",
        "archives",
        Decimal(200 * 1024 * 1024),
    )
    ZLIB = ("application/zlib", ".zlib", "archives", Decimal(50 * 1024 * 1024))

    TXT = ("text/plain", ".txt", "misc", Decimal(5 * 1024 * 1024))
    HTML = ("text/html", ".html", "misc", Decimal(5 * 1024 * 1024))
    PHP = ("text/x-php", ".php", "misc", Decimal(2 * 1024 * 1024))
    MP3 = ("audio/mpeg", ".mp3", "audio", Decimal(50 * 1024 * 1024))
    DOS_EXEC = ("application/x-dosexec", ".exe", "binaries", Decimal(100 * 1024 * 1024))

    def __init__(
        self, mime_type: str, extension: str, category: str, max_size: Decimal
    ):
        self.mime_type = mime_type
        self.extension = extension
        self.category = category
        self.max_size = max_size

    @property
    def label(self):
        return self.name

    @classmethod
    def from_mime(cls, mime: str) -> "FileTypeEnum":
        for ft in cls:
            if ft.mime_type == mime:
                return ft
        raise ValueError(f"No FileType with mime {mime}")

    @classmethod
    def from_extension(cls, ext: str) -> "FileTypeEnum":
        for ft in cls:
            if ft.extension == ext:
                return ft
        raise ValueError(f"No FileType with extension {ext}")
