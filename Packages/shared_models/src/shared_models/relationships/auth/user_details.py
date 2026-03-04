from sqlalchemy.orm import relationship

from ... import UserDetails


UserDetails.user = relationship(
    "User", back_populates="details", uselist=False
)
