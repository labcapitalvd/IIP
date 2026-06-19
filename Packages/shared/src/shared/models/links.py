from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from shared.db import Base, column_fk, column_updated_at
from sqlalchemy.orm import Mapped, relationship

from .targets import TargetTable

if TYPE_CHECKING:
    from .actors import Actor
    from .auth import Role, User
    from .forms import FieldChoice
    from .submissions import AnswerMultiChoice, Submission


class UserFileLink(Base):
    __tablename__ = TargetTable.LINK_USER_FILE.table
    __table_args__ = {"schema": TargetTable.LINK_USER_FILE.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    file_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ROLES.fq_name}.id", nullable=True, ondelete="SET NULL"
    )

    updated_at: Mapped[datetime] = column_updated_at()

    user = relationship("User", back_populates="file_links")
    file = relationship("File", back_populates="user_links")
    role = relationship("Role", back_populates="user_file_link")


class MultiChoiceOptionLink(Base):
    __tablename__ = TargetTable.LINK_CHOICE_MULTICHOICE.table
    __table_args__ = {"schema": TargetTable.LINK_CHOICE_MULTICHOICE.schema}

    choice_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FIELD_CHOICES.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    multi_choice_answer_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ANSWERS_MULTI_CHOICE.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    updated_at: Mapped[datetime] = column_updated_at()

    choice: Mapped["FieldChoice"] = relationship(
        "FieldChoice", back_populates="answer_links"
    )
    answer: Mapped["AnswerMultiChoice"] = relationship(
        "AnswerMultiChoice", back_populates="option_links"
    )


class UserActorLink(Base):
    __tablename__ = TargetTable.LINK_USER_ACTOR.table
    __table_args__ = {"schema": TargetTable.LINK_USER_ACTOR.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    actor_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTORS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ROLES.fq_name}.id", nullable=True, ondelete="SET NULL"
    )

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", back_populates="actor_links")
    actor: Mapped["Actor"] = relationship("Actor", back_populates="user_links")
    role: Mapped["Role"] = relationship("Role")


class UserSubmissionLink(Base):
    __tablename__ = TargetTable.LINK_USER_SUBMISSION.table
    __table_args__ = {"schema": TargetTable.LINK_USER_SUBMISSION.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", primary_key=True, ondelete="CASCADE"
    )
    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ROLES.fq_name}.id", nullable=True, ondelete="SET NULL"
    )

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", back_populates="submission_links")
    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="user_links"
    )
    role: Mapped["Role"] = relationship("Role")
