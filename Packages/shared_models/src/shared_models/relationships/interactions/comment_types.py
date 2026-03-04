from sqlalchemy.orm import relationship

from ... import CommentType


CommentType.comment = relationship(
    "Comment", back_populates="type", uselist=False
)
