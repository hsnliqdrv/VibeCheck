from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Badge(Base):
    """Badge catalog — all available badges in the system"""
    __tablename__ = 'badges'

    id = Column(String, primary_key=True, default=lambda: f"b_{uuid.uuid4().hex[:12]}")
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)          # icon identifier / emoji
    rarity = Column(String(20), nullable=False)        # common | rare | epic | legendary
    category = Column(String(30), nullable=False)      # early | completionist | social | streak | special
    max_progress = Column(Integer, nullable=False, default=1)  # 1 = binary unlock

    # back-ref populated by UserBadge
    user_badges = relationship('UserBadge', back_populates='badge')

    @staticmethod
    def _format_unlocked_date(dt):
        """Format unlocked date in a cross-platform way (no %-d / %-I)."""
        if dt is None:
            return None
        day = dt.day
        hour_12 = dt.hour % 12 or 12
        am_pm = 'AM' if dt.hour < 12 else 'PM'
        return f"{dt.strftime('%B')} {day}, {dt.strftime('%Y')} at {hour_12}:{dt.strftime('%M')} {am_pm}"

    def to_dict(self, unlocked: bool = False, unlocked_date=None, progress: int = 0):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'rarity': self.rarity,
            'category': self.category,
            'maxProgress': self.max_progress,
            'unlocked': unlocked,
            'unlockedDate': self._format_unlocked_date(unlocked_date),
            'progress': progress,
        }

    def __repr__(self):
        return f'<Badge {self.name}>'


class UserBadge(Base):
    """Tracks which badges a user has earned and their progress"""
    __tablename__ = 'user_badges'

    id = Column(String, primary_key=True, default=lambda: f"ub_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    badge_id = Column(String, ForeignKey('badges.id'), nullable=False, index=True)
    unlocked = Column(Boolean, default=False, nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    unlocked_at = Column(DateTime, nullable=True)

    badge = relationship('Badge', back_populates='user_badges')
    user = relationship('User', backref='user_badges')

    def __repr__(self):
        return f'<UserBadge user={self.user_id} badge={self.badge_id}>'


class CuratorLevel(Base):
    """XP-based curator progression levels"""
    __tablename__ = 'curator_levels'

    level = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    xp_required = Column(Integer, nullable=False)
    rewards = Column(JSON, nullable=True)   # list of reward strings
    color = Column(String(7), nullable=True)  # hex e.g. #A855F7

    def to_dict(self):
        return {
            'level': self.level,
            'name': self.name,
            'xpRequired': self.xp_required,
            'rewards': self.rewards or [],
            'color': self.color,
        }

    def __repr__(self):
        return f'<CuratorLevel {self.level} {self.name}>'


# ──────────────────────────────────────────────────────────────────
# Seed data helpers
# ──────────────────────────────────────────────────────────────────

SEED_BADGES = [
    # early
    {'name': 'First Share', 'description': 'Share your first piece of content.', 'icon': '🌱', 'rarity': 'common', 'category': 'early', 'max_progress': 1},
    {'name': 'Early Adopter', 'description': 'Join VibeCheck in its first month.', 'icon': '⚡', 'rarity': 'rare', 'category': 'early', 'max_progress': 1},
    
    # completionist
    {'name': 'Film Buff', 'description': 'Share 10 movies.', 'icon': '🎬', 'rarity': 'common', 'category': 'completionist', 'max_progress': 10},
    {'name': 'Audiophile', 'description': 'Share 10 albums.', 'icon': '🎵', 'rarity': 'common', 'category': 'completionist', 'max_progress': 10},
    {'name': 'Bookworm', 'description': 'Share 10 books.', 'icon': '📚', 'rarity': 'common', 'category': 'completionist', 'max_progress': 10},
    {'name': 'Gamer', 'description': 'Share 10 games.', 'icon': '🎮', 'rarity': 'common', 'category': 'completionist', 'max_progress': 10},
    {'name': 'Wanderer', 'description': 'Share 10 travel locations.', 'icon': '✈️', 'rarity': 'common', 'category': 'completionist', 'max_progress': 10},
    {'name': 'All-Rounder', 'description': 'Share at least one item in every category.', 'icon': '🌈', 'rarity': 'rare', 'category': 'completionist', 'max_progress': 5},
    
    # social
    {'name': 'Social Butterfly', 'description': 'Receive your first aura match.', 'icon': '🦋', 'rarity': 'common', 'category': 'social', 'max_progress': 1},
    {'name': 'Trendsetter', 'description': 'Have 10 posts liked by others.', 'icon': '🔥', 'rarity': 'rare', 'category': 'social', 'max_progress': 10},
    
    # streak
    {'name': '7-Day Streak', 'description': 'Share content 7 days in a row.', 'icon': '📅', 'rarity': 'rare', 'category': 'streak', 'max_progress': 7},
    {'name': '30-Day Streak', 'description': 'Share content 30 days in a row.', 'icon': '🗓️', 'rarity': 'epic', 'category': 'streak', 'max_progress': 30},
    
    # special
    {'name': 'Tastemaker', 'description': 'Reach Curator Level 5.', 'icon': '🏆', 'rarity': 'epic', 'category': 'special', 'max_progress': 1},
    {'name': 'Legend', 'description': 'Reach Curator Level 10.', 'icon': '👑', 'rarity': 'legendary', 'category': 'special', 'max_progress': 1},
]

SEED_CURATOR_LEVELS = [
    {'level': 1, 'name': 'Newcomer',     'xp_required': 0,    'rewards': ['Access to basic features'],                                  'color': '#6B7280'},
    {'level': 2, 'name': 'Explorer',     'xp_required': 100,  'rewards': ['Unlock aura matching'],                                      'color': '#3B82F6'},
    {'level': 3, 'name': 'Curator',      'xp_required': 300,  'rewards': ['Custom aura colors'],                                        'color': '#10B981'},
    {'level': 4, 'name': 'Connoisseur',  'xp_required': 700,  'rewards': ['Profile badge frame'],                                       'color': '#F59E0B'},
    {'level': 5, 'name': 'Tastemaker',   'xp_required': 1500, 'rewards': ['Exclusive Tastemaker badge', 'Priority in aura matches'],    'color': '#8B5CF6'},
    {'level': 6, 'name': 'Visionary',    'xp_required': 3000, 'rewards': ['Visionary profile border'],                                  'color': '#EC4899'},
    {'level': 7, 'name': 'Luminary',     'xp_required': 5000, 'rewards': ['Luminary aura effect'],                                      'color': '#EF4444'},
    {'level': 8, 'name': 'Sage',         'xp_required': 8000, 'rewards': ['Sage curator title'],                                        'color': '#F97316'},
    {'level': 9, 'name': 'Oracle',       'xp_required': 12000,'rewards': ['Oracle discovery feed boost'],                               'color': '#14B8A6'},
    {'level': 10,'name': 'Legend',       'xp_required': 20000,'rewards': ['Legend badge', 'Permanent hall of fame entry'],              'color': '#EAB308'},
]


def seed_badges_and_levels(db):
    """Insert default badges and curator levels if they don't exist yet."""
    # Badges
    for data in SEED_BADGES:
        exists = db.query(Badge).filter_by(name=data['name']).first()
        if not exists:
            badge = Badge(
                id=f"b_{uuid.uuid4().hex[:12]}",
                name=data['name'],
                description=data['description'],
                icon=data['icon'],
                rarity=data['rarity'],
                category=data['category'],
                max_progress=data['max_progress'],
            )
            db.add(badge)

    # Curator levels
    for data in SEED_CURATOR_LEVELS:
        exists = db.query(CuratorLevel).filter_by(level=data['level']).first()
        if not exists:
            lvl = CuratorLevel(**data)
            db.add(lvl)

    db.commit()
