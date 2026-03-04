from sqlalchemy.orm import relationship

from ... import Role


Role.user_file_link = relationship(
    "UserFileLink", back_populates="roles"
)
