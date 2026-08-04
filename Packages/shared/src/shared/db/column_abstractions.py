from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Type, TypeAlias, TypeVar, Union
from uuid import UUID

from sqlalchemy import UUID as UUIDType
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.expression import Function
from sqlalchemy.types import Enum as PgEnum

TEnum = TypeVar("TEnum", bound=Enum)
DateTimeType: TypeAlias = Union[datetime, Function, Callable[[], datetime], None]
DateType: TypeAlias = Union[date, Function, Callable[[], date], None]


def column_fk(
    target: str,
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    primary_key: bool = False,
    ondelete: str | None = None,
    use_alter: bool = False,
    name: str | None = None,
    use_existing_column: bool = False,
    **kwargs: Any,
) -> Mapped[UUID]:
    assert "." in target, "FK target must be 'table.column'"
    return mapped_column(
        UUIDType(as_uuid=True),
        ForeignKey(target, ondelete=ondelete, use_alter=use_alter, name=name),
        nullable=nullable,
        unique=unique,
        index=index,
        primary_key=primary_key,
        use_existing_column=use_existing_column,
        **kwargs,
    )


def column_integer(
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    default: Any = None,
    **kwargs: Any,
) -> Mapped[int]:
    return mapped_column(
        Integer,
        nullable=nullable,
        unique=unique,
        index=index,
        default=default,
        **kwargs,
    )


def column_decimal(
    precision: int = 18,
    scale: int = 4,
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    default: Decimal | None = None,
    **kwargs: Any,
) -> Mapped[Decimal]:
    return mapped_column(
        Numeric(precision=precision, scale=scale),
        nullable=nullable,
        unique=unique,
        index=index,
        default=default,
        **kwargs,
    )


def column_short_text(
    length: int = 255,
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    **kwargs: Any,
) -> Mapped[str]:
    return mapped_column(
        String(length),
        nullable=nullable,
        unique=unique,
        index=index,
        **kwargs,
    )


def column_long_text(
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    **kwargs: Any,
) -> Mapped[str]:
    return mapped_column(
        Text(),
        nullable=nullable,
        unique=unique,
        index=index,
        **kwargs,
    )


def column_datetime(
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    default: DateTimeType = None,
    onupdate: DateTimeType = None,
    use_timezone: bool = True,
    **kwargs: Any,
) -> Mapped[datetime]:
    # Extract server_default from kwargs if explicitly passed, else fallback to func.now()
    server_default = kwargs.pop("server_default", func.now())
    return mapped_column(
        DateTime(timezone=use_timezone),
        nullable=nullable,
        unique=unique,
        index=index,
        default=default,
        onupdate=onupdate,
        server_default=server_default,
        **kwargs,
    )


def column_date(
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    default: DateType = None,
    onupdate: DateType = None,
    **kwargs: Any,
) -> Mapped[date]:
    server_default = kwargs.pop("server_default", func.current_date())
    return mapped_column(
        Date(),
        nullable=nullable,
        unique=unique,
        index=index,
        default=default,
        onupdate=onupdate,
        server_default=server_default,
        **kwargs,
    )


def column_created_at(
    *,
    nullable: bool = False,
    unique: bool = False,
    default: DateTimeType = lambda: datetime.now(timezone.utc),
    **kwargs: Any,
) -> Mapped[datetime]:
    return column_datetime(
        nullable=nullable,
        unique=unique,
        default=default,
        **kwargs,
    )


def column_updated_at(
    *,
    nullable: bool = False,
    unique: bool = False,
    default: DateTimeType = lambda: datetime.now(timezone.utc),
    onupdate: DateTimeType = lambda: datetime.now(timezone.utc),
    **kwargs: Any,
) -> Mapped[datetime]:
    return column_datetime(
        nullable=nullable,
        unique=unique,
        default=default,
        onupdate=onupdate,
        **kwargs,
    )


def column_deleted_at(
    *,
    nullable: bool = True,
    unique: bool = False,
    default: DateTimeType = None,
    onupdate: DateTimeType = None,
    **kwargs: Any,
) -> Mapped[datetime]:
    return column_datetime(
        nullable=nullable,
        unique=unique,
        default=default,
        onupdate=onupdate,
        **kwargs,
    )


def column_uuid(
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    **kwargs: Any,
) -> Mapped[UUID]:
    return mapped_column(
        UUIDType(as_uuid=True),
        nullable=nullable,
        unique=unique,
        index=index,
        **kwargs,
    )


def column_enum(
    enum_cls: Type[TEnum],
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    default: TEnum | Callable[[], TEnum] | None = None,
    name: str | None = None,
    **kwargs: Any,
) -> Mapped[TEnum]:
    return mapped_column(
        PgEnum(
            enum_cls,
            name=name or enum_cls.__name__.lower(),
            create_type=True,
        ),
        nullable=nullable,
        unique=unique,
        index=index,
        default=default,
        **kwargs,
    )


def column_bool(
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    default: bool = False,
    **kwargs: Any,
) -> Mapped[bool]:
    return mapped_column(
        Boolean,
        default=default,
        nullable=nullable,
        unique=unique,
        index=index,
        **kwargs,
    )


def column_slug(
    length: int = 255,
    *,
    nullable: bool = False,
    unique: bool = True,
    index: bool = True,
    **kwargs: Any,
) -> Mapped[str]:
    """Fixed: Added missing String type column specifier."""
    return mapped_column(
        String(length),
        nullable=nullable,
        unique=unique,
        index=index,
        **kwargs,
    )


def column_jsonb(
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = False,
    default: Any = dict,
    **kwargs: Any,
) -> Mapped[dict]:
    """Fixed: Callable factory for JSON dict default."""
    return mapped_column(
        JSONB,
        nullable=nullable,
        unique=unique,
        index=index,
        default=default,
        **kwargs,
    )
