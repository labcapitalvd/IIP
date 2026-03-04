from sqlalchemy.orm import relationship

from ... import RefreshSession


RefreshSession.user = relationship(
    "User", back_populates="refresh_sessions"
)
