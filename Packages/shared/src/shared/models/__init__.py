# Módulo init que carga todos los modelos para simplificar importaciones y prevenir imports circulares.

from .actors import Actor, ActorSegment
from .audit import ActivityLog, LogActionType
from .auth import (
    AccessLevel,
    RefreshSession,
    SystemRole,
    User,
    UserDetails,
    UserProfile,
    UserTier,
)
from .files import File, FileType
from .forms import (
    CardTemplate,
    Field,
    FieldChoice,
    FieldGroup,
    Form,
    Question,
    Section,
    SectionType,
)
from .grading import Criterion, Grade, Result
from .interactions import Comment, CommentType, Notification, NotificationType
from .links import (
    MultiChoiceOptionLink,
    UserActorLink,
    UserFileLink,
    UserSubmissionLink,
    UserSystemRoleLink,
)
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
    # Auth & Security
    "AccessLevel",
    "SystemRole",
    "UserTier",
    "User",
    "RefreshSession",
    "UserDetails",
    "UserProfile",
    # Audit & Files
    "LogActionType",
    "ActivityLog",
    "FileType",
    "File",
    # Interactions
    "CommentType",
    "NotificationType",
    "Comment",
    "Notification",
    # Actors
    "Actor",
    "ActorSegment",
    # Forms
    "CardTemplate",
    "FieldChoice",
    "FieldGroup",
    "Field",
    "Form",
    "Question",
    "Section",
    "SectionType",
    # Grading
    "Criterion",
    "Grade",
    "Result",
    # Links
    "UserFileLink",
    "UserActorLink",
    "UserSubmissionLink",
    "UserSystemRoleLink",
    "MultiChoiceOptionLink",
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
