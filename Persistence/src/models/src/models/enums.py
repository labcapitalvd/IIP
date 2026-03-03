from enum import Enum
from decimal import Decimal


class LogActionTypesEnum(Enum):
    """The logging operations done on update on every table. Trace of what user did what."""
    CREATE = "Se crea una nueva entrada."
    UPDATE = "Se actualiza una entrada."
    DELETE = "Se elimina una entrada."
    GRADE = "Se califica una entrada."
    UPLOAD = "Se carga un archivo."

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


class FileTypesEnum(Enum):
    """Files allowed into the filesystem by the db."""
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


class RolesEnum(Enum):
    """What different roles a user can have in a form."""
    OWNER = "owner"  # Full control over the submission or actor
    CONTRIBUTOR = "contributor"  # Can fill/edit forms, upload files, etc.
    REVIEWER = "reviewer"  # Can comment or suggest changes
    APPROVER = "approver"  # Can finalize and submit
    OBSERVER = "observer"  # Read-only access

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


class UserTiersEnum(Enum):
    """What different priorities and access a user has on the app"""
    ROOT = (Decimal(500 * 1024 * 1024), Decimal(100 * 1024 * 1024 * 1024), 500, 5)
    ADMIN = (Decimal(100 * 1024 * 1024), Decimal(50 * 1024 * 1024 * 1024), 300, 4)
    PREMIUM = (Decimal(50 * 1024 * 1024), Decimal(20 * 1024 * 1024 * 1024), 120, 3)
    STANDARD = (Decimal(10 * 1024 * 1024), Decimal(10 * 1024 * 1024 * 1024), 60, 2)
    GUEST = (Decimal(5 * 1024 * 1024), Decimal(5 * 1024 * 1024 * 1024), 30, 1)

    def __init__(
        self, max_file_size, storage_quota, max_requests_per_minute, priority_level
    ):
        self.max_file_size = max_file_size
        self.storage_quota = storage_quota
        self.max_requests_per_minute = max_requests_per_minute
        self.priority_level = priority_level

    @property
    def label(self):
        return self.name  # Use the enum member name itself


class RuleTypesEnum(Enum):
    """"""
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    REGEX = "regex"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


class RelationalOperatorsEnum(Enum):
    EQUAL = "Dos valores son iguales."
    NOT_EQUAL = "Dos valores son diferentes."
    IS = "Un valor es igual a otro."
    IS_NOT = "Un valor no es igual a otro."
    GREATER_THAN = "Un valor es mayor que otro."
    LESS_THAN = "Un valor es menor que otro."
    GREATER_THAN_OR_EQUAL = "Un valor es mayor o igual que otro."
    LESS_THAN_OR_EQUAL = "Un valor es menor o igual que otro."

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


class SubmissionStatusesEnum(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    NEEDS_REVISION = "needs_revision"
    APPROVED = "approved"
    GRADED = "graded"
    REJECTED = "rejected"
    ASSIGNED = "assigned"
    PARTIALLY_GRADED = "partially_graded"
    AUTO_SUBMITTED = "auto_submitted"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


class FieldTypesEnum(Enum):
    BOOLEAN = "AnswerBoolean"
    CARD = "AnswerCardEntry"
    DATE = "AnswerDate"
    FILE = "AnswerFile"
    MULTI_CHOICE = "AnswerMultiChoice"
    NUMERIC = "AnswerNumeric"
    SINGLE_CHOICE = "AnswerSingleChoice"
    TEXT = "AnswerText"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name  # Use the enum member name itself


class NotificationTypesEnum(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name




class CommentTypesEnum(str, Enum):
    PUBLIC_FEEDBACK = "Alguien dio retroalimentación."
    INTERNAL_NOTE = "Una nota interna"
    REVISION_REQUEST = "Solicitud de revisión"

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name




