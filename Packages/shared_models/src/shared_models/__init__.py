# Módulo init que carga todos los modelos para simplificar importaciones y prevenir imports circulares.

from .enums import (
    LogActionTypesEnum,
    FileTypesEnum,
    RolesEnum,
    UserTiersEnum,
    RuleTypesEnum,
    RelationalOperatorsEnum,
    SubmissionStatusesEnum,
    FieldTypesEnum,
    NotificationTypesEnum,
    CommentTypesEnum,
)

from .actors import Actor, ActorSegment
from .forms import (
    CardTemplate,
    Field,
    FieldChoice,
    FieldGroup,
    Form,
    Info,
    Question,
    Section,
    SectionType,
)
from .grading import Criterion, Grade, Result
from .links import MultiChoiceOptionLink, UserActorLink, UserSubmissionLink
from .reference import FieldType, RelationalOperator, RuleType, SubmissionStatusType
from .rules import FieldDependency, FieldRule, SectionDependency
from .submissions import (
    Answer,
    AnswerBoolean,
    AnswerCardEntry,
    AnswerDate,
    AnswerFile,
    AnswerMultiChoice,
    AnswerNumeric,
    AnswerSingleChoice,
    AnswerText,
    Submission,
)

__all__ = [
    # Enums
    "LogActionTypesEnum",
    "FileTypesEnum",
    "RolesEnum",
    "UserTiersEnum",
    "RuleTypesEnum",
    "RelationalOperatorsEnum",
    "SubmissionStatusesEnum",
    "FieldTypesEnum",
    "NotificationTypesEnum",
    "CommentTypesEnum",
    # Actors
    "Actor",
    "ActorSegment",
    # Forms
    "CardTemplate",
    "FieldChoice",
    "FieldGroup",
    "Field",
    "Form",
    "Info",
    "Question",
    "Section",
    "SectionType",
    # Grading
    "Criterion",
    "Grade",
    "Result",
    # Links
    "MultiChoiceOptionLink",
    "UserActorLink",
    "UserSubmissionLink",
    # Reference
    "FieldType",
    "RelationalOperator",
    "RuleType",
    "SubmissionStatusType",
    # Rules
    "FieldDependency",
    "FieldRule",
    "SectionDependency",
    # Submissions
    "Answer",
    "AnswerBoolean",
    "AnswerCardEntry",
    "AnswerDate",
    "AnswerFile",
    "AnswerMultiChoice",
    "AnswerNumeric",
    "AnswerSingleChoice",
    "AnswerText",
    "Submission",
]
