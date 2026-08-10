from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, relationship

from shared.db import (
    Base,
    column_fk,
    column_integer,
    column_long_text,
    column_short_text,
)

from .targets import TargetTable

if TYPE_CHECKING:
    from .links import UserActorLink
    from .files import Attachment


class ActorSegment(Base):
    """
    Classifies an actor or entity that responds to or interacts with forms.
    """

    __tablename__ = TargetTable.ACTOR_SEGMENTS.table
    __table_args__ = {"schema": TargetTable.ACTOR_SEGMENTS.schema}
    code: Mapped[str] = column_short_text(length=50, unique=True)
    label: Mapped[str] = column_short_text(length=255, unique=True)
    description: Mapped[str | None] = column_long_text(nullable=True)

    actors: Mapped[list["Actor"]] = relationship(
        "Actor", back_populates="actor_segment"
    )


class Actor(Base):
    """
    Represents an actor or organization/entity that answers to a form.
    """

    __tablename__ = TargetTable.ACTORS.table
    __table_args__ = {"schema": TargetTable.ACTORS.schema}

    actor_segment_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTOR_SEGMENTS.fq_name}.id", ondelete="CASCADE"
    )

    sigep_code: Mapped[int | None] = column_integer(nullable=True, unique=True)
    treasury_code: Mapped[int | None] = column_integer(nullable=True, unique=True)
    initials: Mapped[str | None] = column_short_text(
        length=50, nullable=True, unique=True
    )
    code: Mapped[str] = column_short_text(length=50, unique=True)
    label: Mapped[str] = column_short_text(length=255, unique=True)
    description: Mapped[str | None] = column_long_text(nullable=True)
    mission: Mapped[str | None] = column_long_text(nullable=True)
    vision: Mapped[str | None] = column_long_text(nullable=True)

    # Relationships
    actor_segment: Mapped["ActorSegment"] = relationship(
        "ActorSegment", back_populates="actors"
    )
    user_links: Mapped[list["UserActorLink"]] = relationship(
        "UserActorLink", back_populates="actor"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="actor"
    )
