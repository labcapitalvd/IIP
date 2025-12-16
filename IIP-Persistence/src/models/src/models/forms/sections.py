from typing import Optional, List
from uuid import UUID

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, relationship

from shared_db import (
    Base,
    column_fk,
    column_short_text,
    column_integer,
    column_long_text,
)

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class Section(Base):
    __tablename__ = TargetTable.SECTIONS.table
    __table_args__ = (
        Index("idx_sections_form_id", "form_id"),
        Index("idx_sections_parent_id", "parent_id"),
        Index("idx_sections_section_type_id", "section_type_id"),
        Index("idx_sections_parent_display_order", "parent_id", "display_order"),
        {"schema": TargetTable.SECTIONS.schema})

    form_id: Mapped[UUID] = column_fk(target=f"{TargetTable.FORMS.fq_name}.id")
    file_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id", ondelete="CASCADE", nullable=True
    )
    parent_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id",
        ondelete="CASCADE",
        nullable=True,
    )
    section_type_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.SECTION_TYPES.fq_name}.id",
        ondelete="SET NULL",
        nullable=True,
    )

    title: Mapped[str] = column_short_text(255)
    description: Mapped[str] = column_long_text()
    helper: Mapped[str] = column_long_text(nullable=True)
    display_order: Mapped[int] = column_integer(default=0)

    form: Mapped["Form"] = relationship("Form", back_populates="sections")
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="section"
    )
    infos: Mapped[List["Info"]] = relationship("Info", back_populates="section")

    children: Mapped[List["Section"]] = relationship(
        "Section", back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped[Optional["Section"]] = relationship(
        "Section", back_populates="children", remote_side=lambda: Section.id
    )

    type: Mapped["SectionType"] = relationship("SectionType", back_populates="sections")
    dependencies_triggered_by_others: Mapped[List["SectionDependency"]] = relationship(
        "SectionDependency",
        foreign_keys="SectionDependency.target_section_id",
        back_populates="target_section",
    )

    dependencies_it_triggers: Mapped[List["SectionDependency"]] = relationship(
        "SectionDependency",
        foreign_keys="SectionDependency.depends_on_section_id",
        back_populates="depends_on_section",
    )
