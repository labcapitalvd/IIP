from enum import Enum


class LogActionTypesEnum(Enum):
    """The logging operations done on update on every table. Trace of what user did what."""

    # (code, label, description)
    CREATE = ("CREATE", "Crear", "Se crea una nueva entrada.")
    UPDATE = ("UPDATE", "Actualizar", "Se actualiza una entrada.")
    DELETE = ("DELETE", "Eliminar", "Se elimina una entrada.")
    GRADE = ("GRADE", "Calificar", "Se califica una entrada.")
    UPLOAD = ("UPLOAD", "Cargar", "Se carga un archivo.")

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
