from sqlalchemy.orm import relationship

from ... import UserProfile


UserProfile.user = relationship(
    "User", back_populates="profile", uselist=False
)
UserProfile.file = relationship(
    "File", back_populates="profile", uselist=False
)
