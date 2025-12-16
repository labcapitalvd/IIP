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


class RelationalOperator(Base):
    __tablename__ = TargetTable.RELATIONAL_OPERATORS.table
    __table_args__ = {"schema": TargetTable.RELATIONAL_OPERATORS.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    field_dependency: Mapped["FieldDependency"] = relationship(
        "FieldDependency", back_populates="operator_type", uselist=False
    )

    section_dependency: Mapped["SectionDependency"] = relationship(
        "SectionDependency", back_populates="operator_type", uselist=False
    )