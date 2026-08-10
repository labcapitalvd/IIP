# Módulo init que carga todos los modelos para simplificar importaciones y prevenir imports circulares.

from .actors import Actor, ActorSegment
from .audit import ActivityLog, LogActionType
from .auth import (
    Permission,
    RefreshSession,
    ResourceRole,
    SystemRole,
    User,
    UserDetails,
    UserProfile,
    UserTier,
)
from .files import Attachment, File, FileType
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
    ResourceRolePermissionLink,
    SystemRolePermissionLink,
    UserActorLink,
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
    "Permission",
    "ResourceRole",
    "SystemRole",
    "UserTier",
    "User",
    "RefreshSession",
    "UserDetails",
    "UserProfile",
    # Audit & Files
    "LogActionType",
    "ActivityLog",
    "Attachment",
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
    "SystemRolePermissionLink",
    "ResourceRolePermissionLink",
    "UserSystemRoleLink",
    "UserActorLink",
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
