from enum import Enum


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


class RuleTypesEnum(Enum):
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

