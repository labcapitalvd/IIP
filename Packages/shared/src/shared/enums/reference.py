from enum import Enum


class FieldTypesEnum(Enum):
    """
    Maps form field types to their corresponding Answer sub-table.
    Tuple: (code, label, target_answer_model)
    """

    BOOLEAN = ("boolean", "Yes / No Toggle", "AnswerBoolean")
    CARD = ("card", "Card Entry Repeater", "AnswerCardEntry")
    DATE = ("date", "Date Picker", "AnswerDate")
    FILE = ("file", "File Attachment", "AnswerFile")
    MULTI_CHOICE = ("multi_choice", "Multiple Choice Checkboxes", "AnswerMultiChoice")
    NUMERIC = ("numeric", "Numeric Input", "AnswerNumeric")
    SINGLE_CHOICE = ("single_choice", "Single Choice Radio", "AnswerSingleChoice")
    TEXT = ("text", "Free Text Input", "AnswerText")

    def __init__(self, code: str, label: str, target_answer_model: str):
        self.code = code
        self._label = label
        self.target_answer_model = target_answer_model

    @property
    def label(self) -> str:
        return self._label


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
        self.code = code
        self._label = label
        self.description = description

    @property
    def label(self) -> str:
        return self._label


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
        self.code = code
        self._label = label
        self.description = description

    @property
    def label(self) -> str:
        return self._label


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
        self.code = code
        self._label = label
        self.description = description

    @property
    def label(self) -> str:
        return self._label
