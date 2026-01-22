from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_long_text,
    column_fk,
    column_short_text,
    column_integer,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class Info(Base):
    __tablename__ = TargetTable.INFORMATIONS.table
    __table_args__ = {"schema": TargetTable.INFORMATIONS.schema}

    section_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id", ondelete="SET NULL"
    )

    title: Mapped[str] = column_short_text(255)
    description: Mapped[str] = column_long_text()
    file_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id", ondelete="CASCADE", nullable=True
    )

    display_order: Mapped[int] = column_integer(default=0)

    section: Mapped["Section"] = relationship("Section", back_populates="infos")
