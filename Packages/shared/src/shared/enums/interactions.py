from enum import Enum


class NotificationTypesEnum(Enum):
    """
    Notification types matching the NotificationType database model.
    Tuple: (code, label, description)
    """

    INFO = ("info", "Info", "Informational notification.")
    WARNING = ("warning", "Warning", "Warning notification.")
    ERROR = ("error", "Error", "Error notification.")
    SUCCESS = ("success", "Success", "Success notification.")

    def __init__(self, code: str, label: str, description: str):
        self._code = code
        self._label = label
        self._description = description

    @property
    def code(self) -> str:
        return self._code

    @property
    def label(self) -> str:
        return self._label

    @property
    def description(self) -> str:
        return self._description


class CommentTypesEnum(Enum):
    """
    Comment types matching the CommentType database model.
    Tuple: (code, label, description)
    """

    PUBLIC_FEEDBACK = (
        "public_feedback",
        "Public Feedback",
        "Alguien dio retroalimentación.",
    )
    INTERNAL_NOTE = (
        "internal_note",
        "Internal Note",
        "Una nota interna",
    )
    REVISION_REQUEST = (
        "revision_request",
        "Revision Request",
        "Solicitud de revisión",
    )

    def __init__(self, code: str, label: str, description: str):
        self._code = code
        self._label = label
        self._description = description

    @property
    def code(self) -> str:
        return self._code

    @property
    def label(self) -> str:
        return self._label

    @property
    def description(self) -> str:
        return self._description
