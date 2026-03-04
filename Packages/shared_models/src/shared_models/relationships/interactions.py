from sqlalchemy.orm import relationship

from .. import Comment, CommentType, Notification, NotificationType


Comment.user = relationship(
    "User", back_populates="comments"
)
Comment.type = relationship(
    "CommentType", back_populates="comment", uselist=False
)

CommentType.comment = relationship(
    "Comment", back_populates="type", uselist=False
)

Notification.user = relationship(
    "User", back_populates="notifications"
)
Notification.type = relationship(
    "NotificationType", back_populates="notification", uselist=False
)

NotificationType.notification = relationship(
    "Notification", back_populates="type", uselist=False
)
