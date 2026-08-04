from enum import Enum


class FieldTypesEnum(Enum):
    """
    Mapea los tipos de campos de formulario a su tabla secundaria de Respuestas.
    Tupla: (code, label, target_answer_model, description)
    """

    BOOLEAN = (
        "boolean",
        "Opción Sí / No",
        "AnswerBoolean",
        "Campo de alternancia para seleccionar entre Verdadero/Falso o Sí/No.",
    )
    CARD = (
        "card",
        "Repetidor de tarjetas",
        "AnswerCardEntry",
        "Estructura repetible para capturar grupos de datos estructurados.",
    )
    DATE = (
        "date",
        "Selector de fecha",
        "AnswerDate",
        "Campo para seleccionar fechas mediante un calendario.",
    )
    FILE = (
        "file",
        "Archivo adjunto",
        "AnswerFile",
        "Permite adjuntar y subir archivos o documentos.",
    )
    MULTI_CHOICE = (
        "multi_choice",
        "Casillas de selección múltiple",
        "AnswerMultiChoice",
        "Permite seleccionar una o más opciones de una lista predefinida.",
    )
    NUMERIC = (
        "numeric",
        "Entrada numérica",
        "AnswerNumeric",
        "Campo de entrada restringido a valores numéricos (enteros o decimales).",
    )
    SINGLE_CHOICE = (
        "single_choice",
        "Selección única (Radio)",
        "AnswerSingleChoice",
        "Permite seleccionar exactamente una opción de un grupo exclusivo.",
    )
    TEXT = (
        "text",
        "Entrada de texto libre",
        "AnswerText",
        "Entrada de texto libre, soporta palabras, frases o párrafos largos.",
    )

    def __init__(
        self, code: str, label: str, target_answer_model: str, description: str
    ):
        self._code = code
        self._label = label
        self.target_answer_model = target_answer_model
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


class RelationalOperatorsEnum(Enum):
    """Operators used in conditional rule evaluation engines."""

    EQUAL = ("eq", "Equal to", "Dos valores son iguales.")
    NOT_EQUAL = ("ne", "Not equal to", "Dos valores son diferentes.")
    IS = ("is", "Is", "Un valor es igual a otro.")
    IS_NOT = ("is_not", "Is not", "Un valor no es igual a otro.")
    GREATER_THAN = ("gt", "Greater than", "Un valor es mayor que otro.")
    LESS_THAN = ("lt", "Less than", "Un valor es menor que otro.")
    GREATER_THAN_OR_EQUAL = (
        "gte",
        "Greater than or equal to",
        "Un valor es mayor o igual que otro.",
    )
    LESS_THAN_OR_EQUAL = (
        "lte",
        "Less than or equal to",
        "Un valor es menor o igual que otro.",
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


class RuleTypesEnum(Enum):
    """Validation rules applicable to form fields."""

    MIN_LENGTH = (
        "min_length",
        "Minimum Length",
        "Restricts text inputs to a minimum character count.",
    )
    MAX_LENGTH = (
        "max_length",
        "Maximum Length",
        "Restricts text inputs to a maximum character count.",
    )
    REGEX = (
        "regex",
        "Regular Expression",
        "Validates input matching a regex pattern (e.g. Email, URL).",
    )
    MIN_VALUE = (
        "min_value",
        "Minimum Numeric Value",
        "Enforces a floor for numeric entries.",
    )
    MAX_VALUE = (
        "max_value",
        "Maximum Numeric Value",
        "Enforces a ceiling for numeric entries.",
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


class SubmissionStatusesEnum(Enum):
    """Lifecycle workflow states for form submissions."""

    DRAFT = ("draft", "Draft", "Submission is in progress and not yet submitted.")
    SUBMITTED = (
        "submitted",
        "Submitted",
        "Successfully submitted and awaiting review.",
    )
    UNDER_REVIEW = (
        "under_review",
        "Under Review",
        "Currently being reviewed by an assigned evaluator.",
    )
    ASSIGNED = ("assigned", "Assigned", "Assigned to an evaluator for grading.")
    NEEDS_REVISION = (
        "needs_revision",
        "Needs Revision",
        "Returned to submitter for corrections.",
    )
    APPROVED = ("approved", "Approved", "Submission approved by evaluator/approver.")
    PARTIALLY_GRADED = (
        "partially_graded",
        "Partially Graded",
        "Some criteria graded, pending remainder.",
    )
    GRADED = ("graded", "Graded", "All evaluation criteria graded.")
    REJECTED = ("rejected", "Rejected", "Submission rejected.")
    AUTO_SUBMITTED = (
        "auto_submitted",
        "Auto-Submitted",
        "System auto-submitted on expiration or trigger.",
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
