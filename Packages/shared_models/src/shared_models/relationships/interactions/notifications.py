from sqlalchemy.orm import relationship

from ... import Notification


Notification.user = relationship(
    "User", back_populates="notifications"
)
Notification.type = relationship(
    "NotificationType", back_populates="notification", uselist=False
)
