from sqlalchemy.orm import relationship

from .. import File, FileType


File.profile = relationship(
    "UserProfile", back_populates="file", uselist=False
)
File.user_links = relationship(
    "UserFileLink", back_populates="file"
)
File.type = relationship(
    "FileType", back_populates="file", uselist=False
)

FileType.file = relationship(
    "File", back_populates="type", uselist=False
)
