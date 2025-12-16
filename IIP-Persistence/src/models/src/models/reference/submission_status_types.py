from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_short_text, column_long_text

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class SubmissionStatusType(Base):
    __tablename__ = TargetTable.SUBMISSION_STATUS_TYPES.table
    __table_args__ = {"schema": TargetTable.SUBMISSION_STATUS_TYPES.schema}

    label: Mapped[str] = column_short_text(length=255)
    description: Mapped[str] = column_long_text()

    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="status", uselist=False
    )
