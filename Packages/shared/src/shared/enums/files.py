from enum import Enum
from decimal import Decimal


class VisibilityScope(str, Enum):
    PUBLIC = "public"  # Accessible by anyone (e.g., avatar, public branding)
    ACTOR_SCOPED = (
        "actor_scoped"  # Inherits access rules from the parent Actor/Workspace
    )
    PRIVATE = "private"  # Explicitly restricted to owner


class FileTypesEnum(Enum):
    """
    Files allowed into the filesystem by the db.
    Tuple: (code, label, description, mime_type, extension, category, max_size)
    """

    EXCEL_1 = (
        "excel_1",
        "Microsoft Excel 97-2003",
        "Legacy Excel spreadsheet format.",
        "application/vnd.ms-excel",
        ".xls",
        "tabular",
        Decimal(10 * 1024 * 1024),
    )
    EXCEL_2 = (
        "excel_2",
        "Microsoft Excel OpenXML",
        "Modern Excel spreadsheet format.",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
        "tabular",
        Decimal(20 * 1024 * 1024),
    )
    OPEN_EXCEL_1 = (
        "open_excel_1",
        "OpenDocument Spreadsheet",
        "Standard open spreadsheet format.",
        "application/vnd.oasis.opendocument.spreadsheet",
        ".ods",
        "tabular",
        Decimal(10 * 1024 * 1024),
    )
    OPEN_EXCEL_2 = (
        "open_excel_2",
        "OpenDocument Formula/Template",
        "OpenDocument template format.",
        "application/vnd.oasis.opendocument.spreadsheet",
        ".odf",
        "tabular",
        Decimal(10 * 1024 * 1024),
    )
    CSV = (
        "csv",
        "Comma Separated Values",
        "Plain text tabular data format.",
        "text/csv",
        ".csv",
        "tabular",
        Decimal(10 * 1024 * 1024),
    )
    TSV = (
        "tsv",
        "Tab Separated Values",
        "Tab-delimited tabular data format.",
        "text/tab-separated-values",
        ".tsv",
        "tabular",
        Decimal(10 * 1024 * 1024),
    )

    PNG = (
        "png",
        "PNG Image",
        "Lossless compressed image format.",
        "image/png",
        ".png",
        "images",
        Decimal(10 * 1024 * 1024),
    )
    JPEG = (
        "jpeg",
        "JPEG Image",
        "Standard lossy compressed image format.",
        "image/jpeg",
        ".jpg",
        "images",
        Decimal(5 * 1024 * 1024),
    )
    WEBP = (
        "webp",
        "WebP Image",
        "Modern web-optimized image format.",
        "image/webp",
        ".webp",
        "images",
        Decimal(5 * 1024 * 1024),
    )
    GIF = (
        "gif",
        "GIF Image",
        "Indexed-color image and animation format.",
        "image/gif",
        ".gif",
        "images",
        Decimal(5 * 1024 * 1024),
    )
    AVIF = (
        "avif",
        "AVIF Image",
        "High-efficiency next-gen image format.",
        "image/avif",
        ".avif",
        "images",
        Decimal(5 * 1024 * 1024),
    )

    MP4 = (
        "mp4",
        "MP4 Video",
        "Standard MPEG-4 video container.",
        "video/mp4",
        ".mp4",
        "videos",
        Decimal(500 * 1024 * 1024),
    )
    WEBM = (
        "webm",
        "WebM Video",
        "Open web video container format.",
        "video/webm",
        ".webm",
        "videos",
        Decimal(500 * 1024 * 1024),
    )
    MOV = (
        "mov",
        "QuickTime Movie",
        "Apple QuickTime video container.",
        "video/quicktime",
        ".mov",
        "videos",
        Decimal(1 * 1024 * 1024 * 1024),
    )

    PDF = (
        "pdf",
        "PDF Document",
        "Portable Document Format.",
        "application/pdf",
        ".pdf",
        "docs",
        Decimal(50 * 1024 * 1024),
    )
    WORD = (
        "word",
        "Microsoft Word Document",
        "Modern Word document format.",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
        "docs",
        Decimal(20 * 1024 * 1024),
    )
    OPEN_WORD = (
        "open_word",
        "OpenDocument Text",
        "Standard open text document format.",
        "application/vnd.oasis.opendocument.text",
        ".odt",
        "docs",
        Decimal(20 * 1024 * 1024),
    )
    POWERPOINT = (
        "powerpoint",
        "Microsoft PowerPoint Presentation",
        "Modern PowerPoint presentation format.",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
        "docs",
        Decimal(50 * 1024 * 1024),
    )
    OPEN_POWERPOINT = (
        "open_powerpoint",
        "OpenDocument Presentation",
        "Standard open presentation format.",
        "application/vnd.oasis.opendocument.presentation",
        ".odp",
        "docs",
        Decimal(50 * 1024 * 1024),
    )

    ZIP = (
        "zip",
        "ZIP Archive",
        "Standard archive compression format.",
        "application/zip",
        ".zip",
        "archives",
        Decimal(200 * 1024 * 1024),
    )
    RAR = (
        "rar",
        "RAR Archive",
        "RAR compressed archive format.",
        "application/x-rar",
        ".rar",
        "archives",
        Decimal(200 * 1024 * 1024),
    )
    SEVEN_ZIP = (
        "seven_zip",
        "7-Zip Archive",
        "High compression 7z archive format.",
        "application/x-7z-compressed",
        ".7z",
        "archives",
        Decimal(200 * 1024 * 1024),
    )
    ZLIB = (
        "zlib",
        "Zlib Archive",
        "Zlib compressed data stream container.",
        "application/zlib",
        ".zlib",
        "archives",
        Decimal(50 * 1024 * 1024),
    )

    TXT = (
        "txt",
        "Plain Text",
        "Unformatted text file.",
        "text/plain",
        ".txt",
        "misc",
        Decimal(5 * 1024 * 1024),
    )
    HTML = (
        "html",
        "HTML Document",
        "HyperText Markup Language file.",
        "text/html",
        ".html",
        "misc",
        Decimal(5 * 1024 * 1024),
    )
    PHP = (
        "php",
        "PHP Script",
        "PHP source code file.",
        "text/x-php",
        ".php",
        "misc",
        Decimal(2 * 1024 * 1024),
    )
    MP3 = (
        "mp3",
        "MP3 Audio",
        "MPEG audio stream file.",
        "audio/mpeg",
        ".mp3",
        "audio",
        Decimal(50 * 1024 * 1024),
    )
    DOS_EXEC = (
        "dos_exec",
        "Windows Executable",
        "Executable binary file.",
        "application/x-dosexec",
        ".exe",
        "binaries",
        Decimal(100 * 1024 * 1024),
    )

    def __init__(
        self,
        code: str,
        label: str,
        description: str,
        mime_type: str,
        extension: str,
        category: str,
        max_size: Decimal,
    ):
        self._code = code
        self._label = label
        self._description = description
        self.mime_type = mime_type
        self.extension = extension
        self.category = category
        self.max_size = max_size

    @property
    def code(self) -> str:
        return self._code

    @property
    def label(self) -> str:
        return self._label

    @property
    def description(self) -> str:
        return self._description

    @classmethod
    def from_mime(cls, mime: str) -> "FileTypesEnum":
        for ft in cls:
            if ft.mime_type == mime:
                return ft
        raise ValueError(f"No FileType with mime {mime}")

    @classmethod
    def from_extension(cls, ext: str) -> "FileTypesEnum":
        for ft in cls:
            if ft.extension == ext:
                return ft
        raise ValueError(f"No FileType with extension {ext}")
