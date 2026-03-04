from datetime import datetime
from typing import Any, Optional
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
import uuid
from app.database import Base


class Badge(Base):
    """Badge model matching the OpenAPI Badge schema"""
    __tablename__ = 'badges'
    
    id = Column(String, primary_key=True, default=lambda: f"b_{uuid.uuid4().hex[:12]}")
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=False)
    icon = Column(Text, nullable=False)  # URI to badge icon (renamed from image)
    
    # Badge classification
    rarity = Column(String(20), nullable=False, index=True)  # common, rare, epic, legendary
    category = Column(String(50), nullable=False, index=True)  # early, completionist, social, streak, special
    
    # Badge unlock criteria
    unlock_criteria = Column(JSON, nullable=True)  # {type: "shares_count", value: 10}
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user_badges = relationship('UserBadge', back_populates='badge', cascade='all, delete-orphan')
    
    def to_dict(self, user_badge=None) -> dict[str, Any]:
        """Convert badge to dictionary matching OpenAPI Badge schema
        
        Args:
            user_badge: Optional UserBadge instance to include unlock info
        """
        result: dict[str, Any] = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'rarity': self.rarity,
            'category': self.category
        }
        
        # Add user-specific fields if UserBadge provided
        if user_badge:
            result['unlocked'] = True
            result['unlockedDate'] = user_badge.earned_at.strftime('%B %-d, %Y at %-I:%M %p')
            result['progress'] = user_badge.progress if hasattr(user_badge, 'progress') else None
            result['maxProgress'] = user_badge.max_progress if hasattr(user_badge, 'max_progress') else None
        else:
            result['unlocked'] = False
            result['unlockedDate'] = None
            result['progress'] = None
            result['maxProgress'] = None
        
        return result
    
    def __repr__(self):
        return f'<Badge {self.name}>'


class UserBadge(Base):
    """Track which badges a user has earned"""
    __tablename__ = 'user_badges'
    
    id = Column(String, primary_key=True, default=lambda: f"ub_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    badge_id = Column(String, ForeignKey('badges.id'), nullable=False, index=True)
    
    # When user earned the badge
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Progress tracking (optional, for display)
    progress = Column(Integer, nullable=True)
    max_progress = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship('User', backref='earned_badges')
    badge = relationship('Badge', back_populates='user_badges')
    
    def to_dict(self, include_badge=True):
        """Convert user badge to dictionary"""
        result = {
            'id': self.id,
            'earnedAt': self.earned_at.isoformat()
        }
        
        if include_badge and self.badge:
            result['badge'] = self.badge.to_dict(user_badge=self)
        
        return result
    
    def __repr__(self):
        return f'<UserBadge {self.user_id} - {self.badge_id}>'


class CuratorLevel(Base):
    """Curator level definitions for progression system"""
    __tablename__ = 'curator_levels'
    
    id = Column(String, primary_key=True, default=lambda: f"cl_{uuid.uuid4().hex[:12]}")
    level = Column(Integer, nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    xp_required = Column(Integer, nullable=False)  # Total XP needed to reach this level
    icon = Column(Text, nullable=True)  # URI to level icon
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert curator level to dictionary"""
        return {
            'level': self.level,
            'name': self.name,
            'description': self.description,
            'xpRequired': self.xp_required,
            'icon': self.icon
        }
    
    def __repr__(self):
        return f'<CuratorLevel {self.level} - {self.name}>'


class UserCuratorStats(Base):
    """Track user's curator progression and statistics"""
    __tablename__ = 'user_curator_stats'
    
    id = Column(String, primary_key=True, default=lambda: f"ucs_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False, unique=True, index=True)
    
    # Curator progression
    current_level = Column(Integer, default=1, nullable=False)
    current_xp = Column(Integer, default=0, nullable=False)
    total_xp = Column(Integer, default=0, nullable=False)
    
    # Activity statistics
    total_shares = Column(Integer, default=0, nullable=False)
    total_posts = Column(Integer, default=0, nullable=False)
    total_likes_received = Column(Integer, default=0, nullable=False)
    total_comments_received = Column(Integer, default=0, nullable=False)
    
    # Content distribution (counts by category)
    movies_count = Column(Integer, default=0, nullable=False)
    albums_count = Column(Integer, default=0, nullable=False)
    games_count = Column(Integer, default=0, nullable=False)
    books_count = Column(Integer, default=0, nullable=False)
    locations_count = Column(Integer, default=0, nullable=False)
    
    # Community engagement
    followers_count = Column(Integer, default=0, nullable=False)
    following_count = Column(Integer, default=0, nullable=False)
    rooms_joined = Column(Integer, default=0, nullable=False)
    
    # Additional stats for OpenAPI UserStats schema
    streak_days = Column(Integer, default=0, nullable=False)
    completed_filmographies = Column(Integer, default=0, nullable=False)
    finished_books = Column(Integer, default=0, nullable=False)
    early_discoveries = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to User
    user = relationship('User', foreign_keys=[user_id], backref='curator_stats')
    
    def to_dict(self):
        """Convert curator stats to dictionary"""
        return {
            'userId': self.user_id,
            'totalShares': self.total_shares,
            'currentXp': self.current_xp,
            'currentLevel': self.current_level,
            'totalXp': self.total_xp,
            'totalPosts': self.total_posts,
            'totalLikesReceived': self.total_likes_received,
            'totalCommentsReceived': self.total_comments_received,
            'streakDays': self.streak_days,
            'completedFilmographies': self.completed_filmographies,
            'finishedBooks': self.finished_books,
            'earlyDiscoveries': self.early_discoveries,
            'contentDistribution': {
                'movies': self.movies_count,
                'albums': self.albums_count,
                'games': self.games_count,
                'books': self.books_count,
                'locations': self.locations_count
            },
            'community': {
                'followersCount': self.followers_count,
                'followingCount': self.following_count,
                'roomsJoined': self.rooms_joined
            }
        }
    
    def __repr__(self):
        return f'<UserCuratorStats {self.user_id} - Level {self.current_level}>'
