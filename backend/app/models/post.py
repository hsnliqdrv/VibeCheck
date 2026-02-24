from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Post(Base):
    """Social post model matching the OpenAPI MoodboardPost schema"""
    __tablename__ = 'posts'
    
    id = Column(String, primary_key=True, default=lambda: f"p_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    
    # Post content
    category = Column(String(50), nullable=False, index=True)  # cinema, music, games, books, travel
    title = Column(String(255), nullable=False)
    image = Column(Text, nullable=False)  # URI to image
    dominant_color = Column(String(7), nullable=True)  # Hex color code #RRGGBB
    
    # Engagement metrics
    likes = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)

    # Optional room association (nullable = global / non-room post)
    room_id = Column(String, ForeignKey('aesthetic_rooms.id'), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship('User', backref='posts')
    room = relationship('AestheticRoom', back_populates='posts')
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    post_likes = relationship('PostLike', back_populates='post', cascade='all, delete-orphan')
    
    def to_dict(self, include_user=True):
        """Convert post to dictionary"""
        result = {
            'id': self.id,
            'userId': self.user_id,
            'category': self.category,
            'title': self.title,
            'image': self.image,
            'dominantColor': self.dominant_color,
            'timestamp': self.created_at.isoformat(),
            'likes': self.likes,
            'comments': self.comment_count,
            'roomId': self.room_id,
        }
        
        if include_user and self.user:
            result['username'] = self.user.username
            result['userAvatar'] = self.user.avatar
        
        return result
    
    def __repr__(self):
        return f'<Post {self.id} by {self.user_id}>'


class Comment(Base):
    """Comment model matching the OpenAPI Comment schema"""
    __tablename__ = 'comments'
    
    id = Column(String, primary_key=True, default=lambda: f"c_{uuid.uuid4().hex[:12]}")
    post_id = Column(String, ForeignKey('posts.id'), nullable=False, index=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    
    text = Column(Text, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    post = relationship('Post', back_populates='comments')
    user = relationship('User', backref='comments')
    
    def to_dict(self, include_user=True):
        """Convert comment to dictionary"""
        result = {
            'id': self.id,
            'text': self.text,
            'timestamp': self.created_at.isoformat(),
            'likes': self.likes
        }
        
        if include_user and self.user:
            result['userId'] = self.user_id
            result['username'] = self.user.username
            result['userAvatar'] = self.user.avatar
        
        return result
    
    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'


class PostLike(Base):
    """Post like tracking table"""
    __tablename__ = 'post_likes'
    
    id = Column(String, primary_key=True, default=lambda: f"pl_{uuid.uuid4().hex[:12]}")
    post_id = Column(String, ForeignKey('posts.id'), nullable=False, index=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    post = relationship('Post', back_populates='post_likes')
    user = relationship('User', backref='post_likes')
    
    def __repr__(self):
        return f'<PostLike {self.id}>'
