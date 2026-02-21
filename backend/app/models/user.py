from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
import bcrypt
from app.database import Base


class User(Base):
    """User model matching the OpenAPI User schema"""
    __tablename__ = 'users'
    
    user_id = Column(String, primary_key=True, default=lambda: f"u_{uuid.uuid4().hex[:12]}")
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(Text, nullable=True)
    bio = Column(String(500), nullable=True)
    
    # Aura profile fields
    aura_colors = Column(JSON, nullable=True)  # Array of hex color codes
    aesthetic_tags = Column(JSON, nullable=True)  # Array of aesthetic style tags
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def to_dict(self):
        """Convert user to dictionary (exclude password)"""
        return {
            'userId': self.user_id,
            'email': self.email,
            'username': self.username,
            'avatar': self.avatar,
            'bio': self.bio,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
