from sqlalchemy.orm import Mapped

from shared_db import Base, column_long_text, column_short_text

from ...targets import CoreTargetTable as TargetTable

class Role(Base):
    """
    name: canonical role code (matches RoleCode enum)
    """
    __tablename__ = TargetTable.ROLES.table
    __table_args__ = {"schema": TargetTable.ROLES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
