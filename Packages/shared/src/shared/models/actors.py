from shared.db.column_abstractions import column_integer
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from shared.db import Base, column_fk, column_long_text, column_short_text
from sqlalchemy.orm import Mapped, relationship

from .targets import TargetTable

if TYPE_CHECKING:
    from .links import UserActorLink


class Actor(Base):
    '''
    Used to represent an actor or an entity that answers to a form.
    '''

    __tablename__ = TargetTable.ACTORS.table
    __table_args__ = {"schema": TargetTable.ACTORS.schema}

    actor_segment_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTOR_SEGMENTS.fq_name}.id", ondelete="CASCADE"
    )

    sigep_code: Mapped[int] = column_integer(nullable=True, unique=True)
    treasury_code: Mapped[int] = column_integer(nullable=True, unique=True)
    initials: Mapped[str] = column_short_text(length=50, nullable=True, unique=True)
    label: Mapped[str] = column_short_text(length=255, unique=True)
    description: Mapped[str] = column_long_text()
    mission: Mapped[str] = column_long_text()
    vision: Mapped[str] = column_long_text()

    actor_segment: Mapped["ActorSegment"] = relationship(
        "ActorSegment", back_populates="actors"
    )

    user_links: Mapped[list["UserActorLink"]] = relationship(
        "UserActorLink", back_populates="actor"
    )


class ActorSegment(Base):
    '''
    Used to classify an actor or an entity that answers to a form.
    '''

    __tablename__ = TargetTable.ACTOR_SEGMENTS.table
    __table_args__ = {"schema": TargetTable.ACTOR_SEGMENTS.schema}

    label: Mapped[str] = column_short_text(length=255, unique=True)
    description: Mapped[str] = column_long_text()

    actors: Mapped[list["Actor"]] = relationship(
        "Actor", back_populates="actor_segment"
    )
