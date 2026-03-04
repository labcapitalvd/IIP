from uuid import UUID
from datetime import date, datetime, timezone
from enum import Enum
from decimal import Decimal

from typing import TypeVar, Type, Union, Callable, TypeAlias

from sqlalchemy import func, ForeignKey, UUID as UUIDType
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import (
    Text,
    String,
    Boolean,
    Integer,
    Numeric,
    DateTime,
    Date,
    Enum as PgEnum,
)
from sqlalchemy.sql.expression import Function
from sqlalchemy.dialects.postgresql import JSONB

TEnum = TypeVar("TEnum", bound=Enum)
DateTimeType: TypeAlias = Union[datetime, Function, Callable[[], datetime], None]
DateType: TypeAlias = Union[date, Function, Callable[[], date], None]


def column_fk(
    target: str,
    *,
    nullable: bool = False,
    unique: bool = False,
    ondelete: str | None = None,
    index: bool = False,
    primary_key: bool = False,
) -> Mapped[UUID]:
    assert "." in target, "FK target must be 'table.column'"
    return mapped_column(
        UUIDType(as_uuid=True),
        ForeignKey(target, ondelete=ondelete),
        nullable=nullable,
        unique=unique,
        index=index,
        primary_key=primary_key,
    )


def column_integer(
    *, nullable: bool = False, unique: bool = False, default: int | None = None
) -> Mapped[int]:
    return mapped_column(Integer, nullable=nullable, unique=unique, default=default)


def column_decimal(
    precision: int = 18,
    scale: int = 4,
    *,
    nullable: bool = False,
    unique: bool = False,
    default: Decimal | None = None,
) -> Mapped[Decimal]:
    return mapped_column(
        Numeric(precision=precision, scale=scale),
        nullable=nullable,
        unique=unique,
        default=default,
    )


def column_short_text(
    length: int = 255, *, nullable: bool = False, unique: bool = False
) -> Mapped[str]:
    return mapped_column(String(length), nullable=nullable, unique=unique)


def column_long_text(*, nullable: bool = False, unique: bool = False) -> Mapped[str]:
    return mapped_column(Text(), nullable=nullable, unique=unique)


def column_datetime(
    *,
    nullable: bool = False,
    unique: bool = False,
    default: DateTimeType = None,
    onupdate: DateTimeType = None,
    use_timezone: bool = True,
) -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=use_timezone),
        nullable=nullable,
        unique=unique,
        default=default,
        onupdate=onupdate,
        server_default=func.now() if default is None else None,
    )


def column_date(
    *,
    nullable: bool = False,
    unique: bool = False,
    default: DateType = None,
    onupdate: DateType = None,
) -> Mapped[date]:
    return mapped_column(
        Date(),
        nullable=nullable,
        unique=unique,
        default=default,
        onupdate=onupdate,
        server_default=func.current_date() if default is None else None,
    )


def column_created_at(
    *,
    nullable: bool = False,
    unique: bool = False,
    default: DateTimeType = None,
) -> Mapped[datetime]:
    return column_datetime(
        nullable=nullable,
        unique=unique,
        default=default,
    )


def column_updated_at(
    *,
    nullable: bool = False,
    unique: bool = False,
    default: DateTimeType = lambda: datetime.now(timezone.utc),
    onupdate: DateTimeType = lambda: datetime.now(timezone.utc),
) -> Mapped[datetime]:
    return column_datetime(
        nullable=nullable, unique=unique, default=default, onupdate=onupdate
    )


def column_deleted_at(
    *,
    nullable: bool = True,
    unique: bool = False,
    default: DateTimeType = None,
    onupdate: DateTimeType = None,
) -> Mapped[datetime]:
    return column_datetime(
        nullable=nullable, unique=unique, default=default, onupdate=onupdate
    )


def column_uuid() -> Mapped[UUID]:
    return mapped_column(
        UUIDType(as_uuid=True),
    )


def column_enum(
    enum_cls: Type[TEnum],
    *,
    nullable: bool = False,
    default: TEnum | None = None,
    name: str | None = None,
) -> Mapped[TEnum]:
    safe_default = default.value if isinstance(default, Enum) else default
    return mapped_column(
        PgEnum(enum_cls, name=name or enum_cls.__name__.lower(), create_type=True),
        nullable=nullable,
        default=safe_default,
    )


def column_bool(
    *,
    nullable: bool = False,
    unique: bool = False,
    default: bool = False,
) -> Mapped[bool]:
    return mapped_column(Boolean, default=default, nullable=nullable)


def column_slug(
    *, nullable: bool = False, unique: bool = True, index: bool = True
) -> Mapped[str]:
    return mapped_column(nullable=False, unique=unique, index=index)


def column_jsonb(
    *, nullable: bool = False, unique: bool = False, default: dict | None = None
) -> Mapped[dict]:
    return mapped_column(
        JSONB, nullable=nullable, unique=unique, default=default or dict
    )
