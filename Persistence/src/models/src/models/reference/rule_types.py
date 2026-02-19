from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_short_text, column_long_text

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class RuleType(Base):
    """Rule type for field rules. aka minimum length, maximum length, regex, etc."""
    __tablename__ = TargetTable.RULE_TYPES.table
    __table_args__ = {"schema": TargetTable.RULE_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    field_rule: Mapped["FieldRule"] = relationship(
        "FieldRule", back_populates="rule", uselist=False
    )
