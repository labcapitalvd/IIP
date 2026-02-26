# Módulo init que carga todos los modelos para simplificar importaciones y prevenir imports circulares.

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
from .grading import Criteria, Grade, Result
from .links import MultiChoiceOptionLink, UserActorLink, UserSubmissionLink
from .reference import FieldType, RelationalOperator, RuleType, SubmissionStatusType
from .rules import FieldDependency, FieldRule, SectionDependency
from .submissions import (
    Answer,
    BooleanAnswer,
    CardEntry,
    DateAnswer,
    FileAnswer,
    MultiChoiceAnswer,
    NumberAnswer,
    SingleChoiceAnswer,
    Submission,
    TextAnswer,
)

__all__ = [
    "ActorSegment",
    "Actor",
    "UserActorLink",
    
    "FieldType",
    "Form",
    "SectionType",
    "Section",
    "Info",
    "Question",
    "CardTemplate",
    "FieldGroup",
    "Field",
    "FieldChoice",
    
    "RelationalOperator",
    "RuleType",
    "SectionDependency",
    "FieldDependency",
    "FieldRule",
    
    "Submission",
    "SubmissionStatusType",
    "Criteria",
    "Grade",
    "Result",
     
    "CardEntry",
    "Answer",
    "BooleanAnswer",
    "DateAnswer",
    "FileAnswer",
    "MultiChoiceAnswer",
    "NumberAnswer",
    "SingleChoiceAnswer",
    "TextAnswer",
    "UserSubmissionLink",
    "MultiChoiceOptionLink",
]
