from decimal import Decimal

from sqlalchemy.orm import Mapped

from shared_db import Base, column_short_text, column_decimal

from ...targets import CoreTargetTable as TargetTable


class FileType(Base):
    __tablename__ = TargetTable.FILE_TYPES.table
    __table_args__ = {"schema": TargetTable.FILE_TYPES.schema}

    label: Mapped[str] = column_short_text(255)
    mime_type: Mapped[str] = column_short_text(length=255)
    extension: Mapped[str] = column_short_text(length=255)
    category: Mapped[str] = column_short_text(length=255)
    max_size: Mapped[Decimal] = column_decimal(precision=15, scale=0)
