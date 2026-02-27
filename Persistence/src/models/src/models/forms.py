from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from shared_db import (
    Base,
    column_bool,
    column_fk,
    column_integer,
    column_long_text,
    column_short_text,
    column_updated_at,
)
from sqlalchemy import Index, and_
from sqlalchemy.orm import Mapped, foreign, relationship, remote

from models.targets import TargetTable

if TYPE_CHECKING:
    from .grading import Criteria
    from .links import MultiChoiceOptionLink
    from .reference import FieldType
    from .rules import FieldDependency, FieldRule, SectionDependency
    from .submissions import Answer, AnswerCardEntry, AnswerSingleChoice


class CardTemplate(Base):
    __tablename__ = TargetTable.CARD_TEMPLATES.table
    __table_args__ = {"schema": TargetTable.CARD_TEMPLATES.schema}

    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id", ondelete="CASCADE"
    )

    title: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
    helper: Mapped[str] = column_long_text(nullable=True)

    updated_at: Mapped[datetime] = column_updated_at()

    question: Mapped["Question"] = relationship(
        "Question", back_populates="card_templates"
    )
    field_groups: Mapped[List["FieldGroup"]] = relationship(
        "FieldGroup", back_populates="card_template"
    )
    card_entries: Mapped[List["AnswerCardEntry"]] = relationship(
        "CardEntry", back_populates="card_template", cascade="all, delete-orphan"
    )

    criteria: Mapped[List["Criteria"]] = relationship(
        "Criteria",
        primaryjoin=lambda: and_(
            foreign(Criteria.target_id) == remote(Question.id),
            Criteria.target == TargetTable.QUESTIONS.table,
        ),
        viewonly=True,
        overlaps="criteria",
    )


class Field(Base):
    __tablename__ = TargetTable.FIELDS.table
    __table_args__ = {"schema": TargetTable.FIELDS.schema}

    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="SET NULL"
    )
    field_group_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELD_GROUPS.fq_name}.id", ondelete="CASCADE"
    )
    field_type_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELD_TYPES.fq_name}.id", ondelete="CASCADE"
    )

    title: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
    required: Mapped[bool] = column_bool()
    display_order: Mapped[int] = column_integer(default=0)

    updated_at: Mapped[datetime] = column_updated_at()

    field_type: Mapped["FieldType"] = relationship(
        "FieldType", back_populates="field", uselist=False
    )
    field_group: Mapped["FieldGroup"] = relationship(
        "FieldGroup", back_populates="fields"
    )
    field_choices: Mapped[List["FieldChoice"]] = relationship(
        "FieldChoice", back_populates="field"
    )
    field_rules: Mapped[List["FieldRule"]] = relationship(
        "FieldRule", back_populates="field"
    )
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="field")
    dependencies_triggered_by_others: Mapped[List["FieldDependency"]] = relationship(
        "FieldDependency",
        foreign_keys="FieldDependency.target_field_id",
        back_populates="target_field",
    )
    dependencies_it_triggers: Mapped[List["FieldDependency"]] = relationship(
        "FieldDependency",
        foreign_keys="FieldDependency.depends_on_field_id",
        back_populates="depends_on_field",
    )


class FieldChoice(Base):
    __tablename__ = TargetTable.FIELD_CHOICES.table
    __table_args__ = {"schema": TargetTable.FIELD_CHOICES.schema}

    field_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELDS.fq_name}.id", ondelete="CASCADE"
    )

    title: Mapped[str] = column_short_text(255)
    description: Mapped[str] = column_short_text(255)
    display_order: Mapped[int] = column_integer(default=0)

    updated_at: Mapped[datetime] = column_updated_at()

    answer_links: Mapped[list["MultiChoiceOptionLink"]] = relationship(
        "MultiChoiceOptionLink", back_populates="choice"
    )
    answer_link: Mapped["AnswerSingleChoice"] = relationship(
        "SingleChoiceAnswer", back_populates="choice"
    )
    field: Mapped["Field"] = relationship("Field", back_populates="field_choices")


class FieldGroup(Base):
    __tablename__ = TargetTable.FIELD_GROUPS.table
    __table_args__ = {"schema": TargetTable.FIELD_GROUPS.schema}

    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="SET NULL"
    )
    question_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.QUESTIONS.fq_name}.id", ondelete="CASCADE"
    )
    card_template_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.CARD_TEMPLATES.fq_name}.id",
        ondelete="CASCADE",
        nullable=True,
    )

    title: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
    display_order: Mapped[int] = column_integer(default=0)

    updated_at: Mapped[datetime] = column_updated_at()

    question: Mapped["Question"] = relationship(
        "Question", back_populates="field_groups"
    )
    card_template: Mapped["CardTemplate"] = relationship(
        "CardTemplate", back_populates="field_groups"
    )
    fields: Mapped[List["Field"]] = relationship("Field", back_populates="field_group")


class Form(Base):
    __tablename__ = TargetTable.FORMS.table
    __table_args__ = {"schema": TargetTable.FORMS.schema}

    anno: Mapped[int] = column_integer(unique=True)
    name: Mapped[str] = column_short_text()
    description: Mapped[str] = column_long_text()

    sections: Mapped[List["Section"]] = relationship("Section", back_populates="form")


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


class Question(Base):
    __tablename__ = TargetTable.QUESTIONS.table
    __table_args__ = {"schema": TargetTable.QUESTIONS.schema}

    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="SET NULL"
    )
    section_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SECTIONS.fq_name}.id", ondelete="SET NULL"
    )
    is_loop: Mapped[bool] = column_bool()
    file_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id", ondelete="CASCADE", nullable=True
    )

    title: Mapped[str] = column_short_text(255)
    description: Mapped[str] = column_long_text()
    helper: Mapped[str] = column_long_text(nullable=True)
    display_order: Mapped[int] = column_integer(default=0)
    required: Mapped[bool] = column_bool()

    updated_at: Mapped[datetime] = column_updated_at()

    section: Mapped["Section"] = relationship("Section", back_populates="questions")
    field_groups: Mapped[List["FieldGroup"]] = relationship(
        "FieldGroup", back_populates="question"
    )
    card_templates: Mapped[List["CardTemplate"]] = relationship(
        "CardTemplate", back_populates="question"
    )

    criteria: Mapped[List["Criteria"]] = relationship(
        "Criteria",
        primaryjoin=lambda: and_(
            foreign(Criteria.target_id) == Question.id,
            Criteria.target == TargetTable.QUESTIONS.table,
        ),
        viewonly=True,
        overlaps="criteria",
    )


class Section(Base):
    __tablename__ = TargetTable.SECTIONS.table
    __table_args__ = (
        Index("idx_sections_form_id", "form_id"),
        Index("idx_sections_parent_id", "parent_id"),
        Index("idx_sections_section_type_id", "section_type_id"),
        Index("idx_sections_parent_display_order", "parent_id", "display_order"),
        {"schema": TargetTable.SECTIONS.schema},
    )

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


class SectionType(Base):
    __tablename__ = TargetTable.SECTION_TYPES.table
    __table_args__ = {"schema": TargetTable.SECTION_TYPES.schema}

    label: Mapped[str] = column_short_text(255)
    description: Mapped[str] = column_long_text()

    sections: Mapped[List["Section"]] = relationship("Section", back_populates="type")
