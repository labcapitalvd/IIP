from sqlalchemy.orm import relationship

from ... import UserTier


UserTier.user = relationship(
    "User", back_populates="tier", uselist=False
)
