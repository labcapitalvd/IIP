from sqlalchemy.orm import relationship

from ... import LogActionType


LogActionType.log = relationship(
    "ActivityLog", back_populates="type", uselist=False
)
