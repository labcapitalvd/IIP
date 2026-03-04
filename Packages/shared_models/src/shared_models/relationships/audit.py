from sqlalchemy.orm import relationship

from .. import ActivityLog, LogActionType


LogActionType.log = relationship(
    "ActivityLog", back_populates="type", uselist=False
)

ActivityLog.type = relationship(
    "LogActionType", back_populates="log", uselist=False
)
