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


class FileAnswer(Base):
    __tablename__ = TargetTable.ANSWERS_FILE.table
    __table_args__ = {"schema": TargetTable.ANSWERS_FILE.schema}

    answer_id: Mapped[UUID] = column_fk(target=f"{TargetTable.ANSWERS.fq_name}.id")
    value_id: Mapped[UUID] = column_fk(
        target=f"{TargetTable.FILES.fq_name}.id",
        ondelete="CASCADE",
        unique=False,
        nullable=True,
    )

    
    updated_at: Mapped[datetime] = column_updated_at()

    answer: Mapped["Answer"] = relationship("Answer", back_populates="file_answer")
