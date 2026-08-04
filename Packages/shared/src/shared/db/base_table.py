from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import UUID as UUIDType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func  # <-- Import func from sqlalchemy
from uuid_utils import uuid7

from shared.db.column_abstractions import column_uuid


class Base(DeclarativeBase):
    id: Mapped[UUID] = column_uuid(
        primary_key=True,
        server_default=func.gen_random_uuid(),  # <-- Handled entirely by PostgreSQL
    )


ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic base CRUD repository shared across microservices."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, entity: ModelT) -> None:
        self.session.add(entity)

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)

    async def get_by_id(self, id: UUID) -> ModelT | None:
        """Generic PK lookup."""
        return await self.session.get(self.model, id)


@dataclass(frozen=True)
class TableInfo:
    table: str
    schema: str

    @property
    def fq_name(self) -> str:
        return f"{self.schema}.{self.table}"


def generate_table_enum(name: str, *registries) -> type[Enum]:
    members = {}
    for registry in registries:
        for key, value in registry.__dict__.items():
            if key.isupper() and isinstance(value, TableInfo):
                members[key] = value.fq_name

    return StrEnum(name, members)
