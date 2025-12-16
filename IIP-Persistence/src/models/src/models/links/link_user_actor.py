from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_fk, column_updated_at

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
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
