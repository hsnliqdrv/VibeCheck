from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Share(Base):
    """User content share model matching the OpenAPI UserShare schema"""
    __tablename__ = 'shares'
    
    id = Column(String, primary_key=True, default=lambda: f"s_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    
    # Content reference
    category = Column(String(50), nullable=False, index=True)  # cinema, music, games, books, travel
    content_id = Column(String(100), nullable=False)  # ID from external API
    title = Column(String(255), nullable=False)
    
    # Optional metadata
    image = Column(Text, nullable=True)  # URI to cover/poster image
    dominant_color = Column(String(7), nullable=True)  # Hex color code #RRGGBB
    caption = Column(String(500), nullable=True)  # User's caption/note
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship to User
    user = relationship('User', backref='shares')
    
    def to_dict(self):
        """Convert share to dictionary"""
        return {
            'id': self.id,
            'userId': self.user_id,
            'category': self.category,
            'contentId': self.content_id,
            'title': self.title,
            'image': self.image,
            'dominantColor': self.dominant_color,
            'caption': self.caption,
            'timestamp': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Share {self.id} by {self.user_id}>'
