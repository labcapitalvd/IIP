from sqlalchemy.orm import relationship

from ... import FileType


FileType.file = relationship(
    "File", back_populates="type", uselist=False
)
