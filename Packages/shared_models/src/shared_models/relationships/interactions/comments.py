from sqlalchemy.orm import relationship

from ... import Comment


Comment.user = relationship(
    "User", back_populates="comments"
)
Comment.type = relationship(
    "CommentType", back_populates="comment", uselist=False
)
