from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
import hashlib
import secrets
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
    
    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)  # hashed token
    verification_token_expiry = Column(DateTime, nullable=True)
    
    # Password reset
    reset_token = Column(String(255), nullable=True)  # hashed token
    reset_token_expiry = Column(DateTime, nullable=True)
    reset_token_used = Column(Boolean, default=False, nullable=False)
    
    # Social media links
    social_media_links = Column(JSON, nullable=True)  # Array of {platform, url}
    
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
    
    def generate_verification_token(self):
        """Generate an email verification token. Returns the raw token (to send to user)."""
        raw_token = secrets.token_urlsafe(32)
        self.verification_token = hashlib.sha256(raw_token.encode()).hexdigest()
        self.verification_token_expiry = datetime.utcnow() + timedelta(hours=24)
        return raw_token
    
    def generate_reset_token(self):
        """Generate a password reset token. Returns the raw token (to send to user)."""
        raw_token = secrets.token_urlsafe(32)
        self.reset_token = hashlib.sha256(raw_token.encode()).hexdigest()
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        self.reset_token_used = False
        return raw_token
    
    @staticmethod
    def hash_token(raw_token):
        """Hash a raw token for comparison."""
        return hashlib.sha256(raw_token.encode()).hexdigest()
    
    def to_dict(self):
        """Convert user to dictionary (exclude password)"""
        return {
            'userId': self.user_id,
            'email': self.email,
            'username': self.username,
            'avatar': self.avatar,
            'bio': self.bio,
            'emailVerified': self.email_verified,
            'socialMediaLinks': self.social_media_links or [],
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
