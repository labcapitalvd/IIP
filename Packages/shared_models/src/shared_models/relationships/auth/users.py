from sqlalchemy.orm import relationship

from ... import User


User.profile = relationship(
    "UserProfile", back_populates="user", uselist=False
)
User.details = relationship(
    "UserDetails", back_populates="user", uselist=False
)
User.tier = relationship(
    "UserTier", back_populates="user", uselist=False
)
User.notifications = relationship(
    "Notification", back_populates="user"
)
User.comments = relationship(
    "Comment", back_populates="user"
)
User.file_links = relationship(
    "UserFileLink", back_populates="user"
)
User.refresh_sessions = relationship(
    "RefreshSession", back_populates="user"
)
