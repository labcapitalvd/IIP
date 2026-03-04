from dataclasses import dataclass
from uuid import UUID
from uuid_utils import uuid7
from enum import Enum
from typing import cast

from sqlalchemy import UUID as UUIDType
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(
        UUIDType(as_uuid=True),
        primary_key=True,
        default=lambda: UUID(str(uuid7())),
    )

@dataclass(frozen=True)
class TableInfo:
    table: str
    schema: str

    @property
    def fq_name(self) -> str:
        return f"{self.schema}.{self.table}"

