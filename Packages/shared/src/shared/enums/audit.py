from enum import Enum


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

