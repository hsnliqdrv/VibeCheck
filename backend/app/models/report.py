from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class RoomPostReport(Base):
    """Report submitted for a post inside a room."""
    __tablename__ = 'post_reports'

    id = Column(String, primary_key=True, default=lambda: f"pr_{uuid.uuid4().hex[:12]}")
    room_id = Column(String, ForeignKey('aesthetic_rooms.id'), nullable=False, index=True)
    post_id = Column(String, ForeignKey('posts.id'), nullable=False, index=True)
    reporter_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    post_owner_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    room = relationship('AestheticRoom')
    post = relationship('Post')
    reporter = relationship('User', foreign_keys=[reporter_id])
    post_owner = relationship('User', foreign_keys=[post_owner_id])

    def to_dict(self):
        return {
            'id': self.id,
            'roomId': self.room_id,
            'postId': self.post_id,
            'reporterId': self.reporter_id,
            'ownerId': self.post_owner_id,
            'reason': self.reason,
            'createdAt': self.created_at.isoformat(),
        }
