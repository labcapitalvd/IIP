# shared_schemas/__init__.py
# Unified exports for schemas, avoiding circular imports.

from .base.base import (
    BaseSchema,
    ResponseMessageSchema,
    UuidSchema,
    LabelSchema,
    DescriptionSchema,
    HelperSchema,
    DisplayOrderSchema,
    RequiredSchema,
)

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
    # base
    ActorSchema,
    ActorSegmentSchema,
    # fk
    ActorSchemaFK,
    ActorSegmentSchemaFK,
    # rel
    ActorSchemaRel,
    ActorSegmentSchemaRel,
    # extended
    ActorSchemaExtended,
    ActorSegmentSchemaExtended,
)


from .core.forms import (
    # base
    CardTemplateSchema,
    FieldSchema,
    FieldChoiceSchema,
    FieldGroupSchema,
    FormSchema,
    InfoSchema,
    QuestionSchema,
    SectionSchema,
    # fk
    CardTemplateSchemaFK,
    FieldSchemaFK,
    FieldChoiceSchemaFK,
    FieldGroupSchemaFK,
    FormSchemaFK,
    InfoSchemaFK,
    QuestionSchemaFK,
    SectionSchemaFK,
    # rel
    CardTemplateSchemaRel,
    FieldSchemaRel,
    FieldChoiceSchemaRel,
    FieldGroupSchemaRel,
    FormSchemaRel,
    InfoSchemaRel,
    QuestionSchemaRel,
    SectionSchemaRel,
    # extended
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
    "ResponseMessageSchema",
    "UuidSchema",
    "LabelSchema",
    "DescriptionSchema",
    "HelperSchema",
    "DisplayOrderSchema",
    "RequiredSchema",
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
