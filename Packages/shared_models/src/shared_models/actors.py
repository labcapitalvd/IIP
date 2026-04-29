from typing import Optional, TYPE_CHECKING
from uuid import UUID

from shared_db import Base, column_fk, column_long_text, column_short_text
from sqlalchemy.orm import Mapped, relationship

from models.targets import TargetTable
if TYPE_CHECKING:
    from .links import UserActorLink

class Actor(Base):
    __tablename__ = TargetTable.ACTORS.table
    __table_args__ = {"schema": TargetTable.ACTORS.schema}

    actor_segment_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTOR_SEGMENTS.fq_name}.id", ondelete="CASCADE"
    )
    contact_person_id: Mapped[Optional[UUID]] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id", ondelete="SET NULL", nullable=True
    )

    name: Mapped[str] = column_short_text(length=255, unique=True)
    description: Mapped[str] = column_long_text()
    mission: Mapped[str] = column_long_text()
    vision: Mapped[str] = column_long_text()

    actor_segment: Mapped["ActorSegment"] = relationship(
        "ActorSegment", back_populates="actors"
    )

    user_links: Mapped["UserActorLink"] = relationship(
        "UserActorLink", back_populates="actor"
    )


class ActorSegment(Base):
    __tablename__ = TargetTable.ACTOR_SEGMENTS.table
    __table_args__ = {"schema": TargetTable.ACTOR_SEGMENTS.schema}

    name: Mapped[str] = column_short_text(length=255, unique=True)
    description: Mapped[str] = column_long_text()

    actors: Mapped[list["Actor"]] = relationship(
        "Actor", back_populates="actor_segment"
    )
