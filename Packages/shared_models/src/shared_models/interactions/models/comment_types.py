from sqlalchemy.orm import Mapped

from shared_db import Base, column_long_text, column_short_text

from ...targets import CoreTargetTable as TargetTable

class CommentType(Base):
    __tablename__ = TargetTable.COMMENT_TYPES.table
    __table_args__ = {"schema": TargetTable.COMMENT_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()
