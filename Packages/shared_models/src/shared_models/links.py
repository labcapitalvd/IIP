from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING

from shared_db import (
    Base,
    column_fk,
    column_updated_at,
)
from sqlalchemy.orm import Mapped, relationship

from models.targets import TargetTable

if TYPE_CHECKING:
    from .submissions import (
        AnswerMultiChoice,
        Submission,
    )
    from .forms import FieldChoice
    from .actors import Actor
    from shared_models import User, Role


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
        target=f"{TargetTable.USERS.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    actor_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTORS.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ROLES.fq_name}.id",
        primary_key=True,
        ondelete="SET NULL",
    )

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", backref="actor_links")
    actor: Mapped["Actor"] = relationship("Actor", back_populates="user_links")
    roles: Mapped["Role"] = relationship("Role", backref="user_actor_link")


class UserSubmissionLink(Base):
    __tablename__ = TargetTable.LINK_USER_SUBMISSION.table
    __table_args__ = {"schema": TargetTable.LINK_USER_SUBMISSION.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", primary_key=True
    )
    submission_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSIONS.fq_name}.id", primary_key=True
    )
    role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ROLES.fq_name}.id",
        primary_key=True,
        ondelete="SET NULL",
    )

    updated_at: Mapped[datetime] = column_updated_at()

    user: Mapped["User"] = relationship("User", backref="submission_links")
    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="user_links"
    )
    roles: Mapped["Role"] = relationship("Role", backref="user_submission_link")
