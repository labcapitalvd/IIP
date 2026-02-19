# Módulo init que carga todos los modelos para simplificar importaciones y prevenir imports circulares.

from .actors.actor_segments import ActorSegment
from .actors.actors import Actor
from .links.link_user_actor import UserActorLink

from .reference.field_types import FieldType
from .forms.forms import Form
from .forms.section_types import SectionType
from .forms.sections import Section
from .forms.informations import Info
from .forms.questions import Question
from .forms.card_templates import CardTemplate
from .forms.field_groups import FieldGroup
from .forms.fields import Field
from .forms.field_choices import FieldChoice

from .reference.relational_operators import RelationalOperator
from .reference.rule_types import RuleType
from .rules.section_dependencies import SectionDependency
from .rules.field_dependencies import FieldDependency
from .rules.field_rules import FieldRule

from .reference.submission_status_types import SubmissionStatusType
from .submissions.submissions import Submission
from .grading.criteria import Criteria
from .grading.grades import Grade
from .grading.results import Result

from .submissions.answers_card_entry import CardEntry
from .submissions.answers import Answer
from .submissions.answers_boolean import BooleanAnswer
from .submissions.answers_date import DateAnswer
from .submissions.answers_file import FileAnswer
from .submissions.answers_multi_choice import MultiChoiceAnswer
from .submissions.answers_numeric import NumberAnswer
from .submissions.answers_single_choice import SingleChoiceAnswer
from .submissions.answers_text import TextAnswer
from .links.link_user_submission import UserSubmissionLink
from .links.link_multichoices_choices import MultiChoiceOptionLink

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
