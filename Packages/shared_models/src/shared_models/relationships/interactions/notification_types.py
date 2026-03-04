from sqlalchemy.orm import relationship

from ... import NotificationType


NotificationType.notification = relationship(
    "Notification", back_populates="type", uselist=False
)
