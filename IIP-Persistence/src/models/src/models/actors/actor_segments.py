from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_long_text, column_short_text

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)
print("Merged TargetTable members:")
for m in TargetTable:
    print(m.name, m.table, m.schema)


class ActorSegment(Base):
    __tablename__ = TargetTable.ACTOR_SEGMENTS.table
    __table_args__ = {"schema": TargetTable.ACTOR_SEGMENTS.schema}

    name: Mapped[str] = column_short_text(length=255, unique=True)
    description: Mapped[str] = column_long_text()

    actors: Mapped[list["Actor"]] = relationship("Actor", back_populates="actor_segment")
