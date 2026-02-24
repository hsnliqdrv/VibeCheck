from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Text, ForeignKey, Integer, Boolean,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class AestheticRoom(Base):
    """
    Aesthetic community room where users can gather around a shared vibe
    and post content.  Matches the OpenAPI AestheticRoom schema.
    """
    __tablename__ = 'aesthetic_rooms'

    id = Column(
        String, primary_key=True,
        default=lambda: f"r_{uuid.uuid4().hex[:12]}",
    )
    name = Column(String(100), nullable=False)
    hashtag = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    cover_gradient = Column(String(200), nullable=True)

    # Counters (kept in sync on join/leave/post)
    member_count = Column(Integer, default=0, nullable=False)
    post_count = Column(Integer, default=0, nullable=False)
    trending = Column(Boolean, default=False, nullable=False)

    # JSON array of moderator user_ids
    moderators = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow,
        onupdate=datetime.utcnow, nullable=False,
    )

    # Relationships
    members = relationship(
        'RoomMember', back_populates='room',
        cascade='all, delete-orphan',
    )
    posts = relationship('Post', back_populates='room', lazy='dynamic')

    def to_dict(self, include_posts: bool = False) -> dict:
        result: dict = {
            'id': self.id,
            'name': self.name,
            'hashtag': self.hashtag,
            'description': self.description,
            'coverGradient': self.cover_gradient,
            'memberCount': self.member_count,
            'postCount': self.post_count,
            'trending': self.trending,
            'moderators': self.moderators or [],
        }
        if include_posts:
            result['posts'] = [p.to_dict() for p in self.posts]
        return result

    def __repr__(self) -> str:
        return f'<AestheticRoom {self.hashtag}>'


class RoomMember(Base):
    """Tracks which users have joined which rooms and when."""
    __tablename__ = 'room_members'

    id = Column(
        String, primary_key=True,
        default=lambda: f"rm_{uuid.uuid4().hex[:12]}",
    )
    room_id = Column(
        String, ForeignKey('aesthetic_rooms.id'),
        nullable=False, index=True,
    )
    user_id = Column(
        String, ForeignKey('users.user_id'),
        nullable=False, index=True,
    )
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    room = relationship('AestheticRoom', back_populates='members')
    user = relationship('User', backref='room_memberships')

    def __repr__(self) -> str:
        return f'<RoomMember user={self.user_id} room={self.room_id}>'
