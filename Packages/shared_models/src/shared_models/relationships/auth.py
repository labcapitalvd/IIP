from sqlalchemy.orm import relationship

from .. import Role, User, UserDetails, UserProfile, UserTier, RefreshSession


Role.user_file_link = relationship(
    "UserFileLink", back_populates="roles"
)

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

UserDetails.user = relationship(
    "User", back_populates="details", uselist=False
)

UserProfile.user = relationship(
    "User", back_populates="profile", uselist=False
)
UserProfile.file = relationship(
    "File", back_populates="profile", uselist=False
)

UserTier.user = relationship(
    "User", back_populates="tier", uselist=False
)

RefreshSession.user = relationship(
    "User", back_populates="refresh_sessions"
)
