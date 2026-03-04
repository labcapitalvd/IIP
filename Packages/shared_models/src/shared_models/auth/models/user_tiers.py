from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Mapped

from shared_db import (
    Base,
    column_updated_at,
    column_decimal,
    column_integer,
    column_short_text,
)

from ...targets import CoreTargetTable as TargetTable

class UserTier(Base):
    __tablename__ = TargetTable.USER_TIERS.table
    __table_args__ = {"schema": TargetTable.USER_TIERS.schema}

    label: Mapped[str] = column_short_text(50)
    max_file_size: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    storage_quota: Mapped[Decimal] = column_decimal(precision=15, scale=0)
    max_requests_per_minute: Mapped[int] = column_integer()
    priority_level: Mapped[int] = column_integer()

    
    updated_at: Mapped[datetime] = column_updated_at()
