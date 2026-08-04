# ../Packages/shared/src/shared/models/mixins.py
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text

from shared.db.column_abstractions import column_short_text, column_long_text


class CodeLabelDescriptionMixin:
    """Mixin for models that require a code, label, and description."""

    code: Mapped[str | None] = column_short_text(length=50, nullable=True, index=True)
    label: Mapped[str | None] = column_short_text(length=255, nullable=True)
    description: Mapped[str | None] = column_long_text(nullable=True)
