from dataclasses import dataclass
from enum import Enum
from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import UUID as UUIDType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid_utils import uuid7


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(
        UUIDType(as_uuid=True),
        primary_key=True,
        default=lambda: UUID(str(uuid7())),
    )


ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Generic base CRUD repository shared across microservices."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, entity: ModelT) -> None:
        self.session.add(entity)

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)


@dataclass(frozen=True)
class TableInfo:
    table: str
    schema: str

    @property
    def fq_name(self) -> str:
        return f"{self.schema}.{self.table}"


def generate_table_enum(name, *registries) -> Type[Enum]:
    members = {}
    for registry in registries:
        # Get all upper-case attributes that are TableInfo instances
        for key, value in registry.__dict__.items():
            if key.isupper() and isinstance(value, TableInfo):
                # Use fq_name as the value stored in the DB
                members[key] = value.fq_name
    return Enum(name, members)
