from sqlalchemy.orm import relationship

from ... import File


File.profile = relationship(
    "UserProfile", back_populates="file", uselist=False
)
File.user_links = relationship(
    "UserFileLink", back_populates="file"
)
File.type = relationship(
    "FileType", back_populates="file", uselist=False
)
