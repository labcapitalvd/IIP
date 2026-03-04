from sqlalchemy.orm import relationship

from ... import ActivityLog


ActivityLog.type = relationship(
    "LogActionType", back_populates="log", uselist=False
)
