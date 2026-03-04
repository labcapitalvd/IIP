from sqlalchemy.orm import relationship

from ... import UserFileLink


UserFileLink.user = relationship(
    "User", back_populates="file_links"
)
UserFileLink.file = relationship(
    "File", back_populates="user_links"
)
UserFileLink.roles = relationship(
    "Role", back_populates="user_file_link"
)
