from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped

from shared_db import Base, column_fk, column_updated_at

from ...targets import CoreTargetTable as TargetTable

class UserFileLink(Base):
    __tablename__ = TargetTable.LINK_USER_FILE.table
    __table_args__ = {"schema": TargetTable.LINK_USER_FILE.schema}

    user_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.USERS.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    file_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    role_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ROLES.fq_name}.id",
        primary_key=True,
        ondelete="SET NULL",
    )

    updated_at: Mapped[datetime] = column_updated_at()
