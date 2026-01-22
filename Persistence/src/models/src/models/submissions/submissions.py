from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship

from shared_db import Base, column_fk, column_updated_at

from shared_models.targets import TargetTable as TargetTableBase
from models.targets import TargetTable as TargetTableApp

from shared_db import merge_enums

TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


class Submission(Base):
    __tablename__ = TargetTable.SUBMISSIONS.table
    __table_args__ = {"schema": TargetTable.SUBMISSIONS.schema}

    actor_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.ACTORS.fq_name}.id", ondelete="SET NULL"
    )
    form_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FORMS.fq_name}.id", ondelete="SET NULL"
    )
    status_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.SUBMISSION_STATUS_TYPES.fq_name}.id",
        ondelete="SET NULL",
    )

    
    updated_at: Mapped[datetime] = column_updated_at()

    status: Mapped["SubmissionStatusType"] = relationship(
        "SubmissionStatusType", back_populates="submission", uselist=False
    )

    user_links: Mapped["UserSubmissionLink"] = relationship(
        "UserSubmissionLink", back_populates="submission"
    )
    card_entries: Mapped["CardEntry"] = relationship(
        "CardEntry", back_populates="submission"
    )
    answers: Mapped["Answer"] = relationship("Answer", back_populates="submission")
