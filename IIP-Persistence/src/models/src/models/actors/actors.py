from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_long_text, column_short_text, column_fk

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


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

    actor_segment: Mapped["ActorSegment"] = relationship("ActorSegment", back_populates="actors")

    user_links: Mapped["UserActorLink"] = relationship(
        "UserActorLink", back_populates="actor"
    )
