# shared_schemas/__init__.py
# Unified exports for schemas, avoiding circular imports.

from .base.base import (
    BaseSchema,
    UuidSchema,
    LabelSchema,
    DescriptionSchema,
    HelperSchema,
    DisplayOrderSchema,
    RequiredSchema,
    ResponseMessageSchema,
)

# auth depends on base, so import it *after* base
from .auth.auth import (
    UsernameSchema,
    UserEmailSchema,
    UserPasswordSchema,
    PlatformSchema,
    AccessTokenSchema,
    RefreshTokenSchema,
    ResponseAuthSchema,
)

from .core.actors import (
    ActorSchema,
    ActorSegmentSchema,
)
from .core.actors import (
    ActorSchemaFK,
    ActorSegmentSchemaFK,
)
from .core.actors import (
    ActorSchemaRel,
    ActorSegmentSchemaRel,
)
from .core.actors import (
    ActorSchemaExtended,
    ActorSegmentSchemaExtended,
)


from .core.forms import (
    CardTemplateSchema,
    FieldSchema,
    FieldChoiceSchema,
    FieldGroupSchema,
    FormSchema,
    InfoSchema,
    QuestionSchema,
    SectionSchema,
)
from .core.forms import (
    CardTemplateSchemaFK,
    FieldSchemaFK,
    FieldChoiceSchemaFK,
    FieldGroupSchemaFK,
    FormSchemaFK,
    InfoSchemaFK,
    QuestionSchemaFK,
    SectionSchemaFK,
)
from .core.forms import (
    CardTemplateSchemaRel,
    FieldSchemaRel,
    FieldChoiceSchemaRel,
    FieldGroupSchemaRel,
    FormSchemaRel,
    InfoSchemaRel,
    QuestionSchemaRel,
    SectionSchemaRel,
)
from .core.forms import (
    CardTemplateSchemaExtended,
    FieldSchemaExtended,
    FieldChoiceSchemaExtended,
    FieldGroupSchemaExtended,
    FormSchemaExtended,
    InfoSchemaExtended,
    QuestionSchemaExtended,
    SectionSchemaExtended,
)

__all__ = [
    # errors
    "CustomError",
    "ItemError",
    "ResponseError",
    "custom_error_handler",
    "add_custom_error_responses",
    "add_routers_with_custom_errors",
    # base
    "BaseSchema",
    "UuidSchema",
    "LabelSchema",
    "DescriptionSchema",
    "HelperSchema",
    "DisplayOrderSchema",
    "RequiredSchema",
    "ResponseMessageSchema",
    # auth
    "UsernameSchema",
    "UserEmailSchema",
    "UserPasswordSchema",
    "PlatformSchema",
    "AccessTokenSchema",
    "RefreshTokenSchema",
    "ResponseAuthSchema",
    # core base
    "ActorSchema",
    "ActorSegmentSchema",
    "CardTemplateSchema",
    "FieldSchema",
    "FieldChoiceSchema",
    "FieldGroupSchema",
    "FormSchema",
    "InfoSchema",
    "QuestionSchema",
    "SectionSchema",
    # core fk
    "ActorSchemaFK",
    "ActorSegmentSchemaFK",
    "CardTemplateSchemaFK",
    "FieldSchemaFK",
    "FieldChoiceSchemaFK",
    "FieldGroupSchemaFK",
    "FormSchemaFK",
    "InfoSchemaFK",
    "QuestionSchemaFK",
    "SectionSchemaFK",
    # core rel
    "ActorSchemaRel",
    "ActorSegmentSchemaRel",
    "CardTemplateSchemaRel",
    "FieldSchemaRel",
    "FieldChoiceSchemaRel",
    "FieldGroupSchemaRel",
    "FormSchemaRel",
    "InfoSchemaRel",
    "QuestionSchemaRel",
    "SectionSchemaRel",
    # core extended
    "ActorSchemaExtended",
    "ActorSegmentSchemaExtended",
    "CardTemplateSchemaExtended",
    "FieldSchemaExtended",
    "FieldChoiceSchemaExtended",
    "FieldGroupSchemaExtended",
    "FormSchemaExtended",
    "InfoSchemaExtended",
    "QuestionSchemaExtended",
    "SectionSchemaExtended",
]
