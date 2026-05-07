from enum import Enum


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
