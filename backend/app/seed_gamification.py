"""
Seed script for VibeCheck gamification data
Creates sample badges and curator levels
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import get_db
from app.models.gamification import Badge, CuratorLevel


def seed_badges(db):
    """Create sample badges in the database"""
    
    # OpenAPI spec: rarity [common, rare, epic, legendary]
    # OpenAPI spec: category [early, completionist, social, streak, special]
    
    badges_data = [
        # Early badges - for starting activities
        {
            'name': 'First Steps',
            'description': 'Created your first share',
            'icon': '/badges/first_steps.png',
            'rarity': 'common',
            'category': 'early',
            'unlock_criteria': {'type': 'shares_count', 'value': 1}
        },
        {
            'name': 'Getting Started',
            'description': 'Created 5 shares',
            'icon': '/badges/getting_started.png',
            'rarity': 'common',
            'category': 'early',
            'unlock_criteria': {'type': 'shares_count', 'value': 5}
        },
        {
            'name': 'Early Adopter',
            'description': 'One of the first to join VibeCheck',
            'icon': '/badges/early_adopter.png',
            'rarity': 'rare',
            'category': 'early',
            'unlock_criteria': {'type': 'early_user', 'value': 1000}
        },
        
        # Completionist badges - for completing collections
        {
            'name': 'Diverse Curator',
            'description': 'Shared content from all 5 categories',
            'icon': '/badges/diverse_curator.png',
            'rarity': 'rare',
            'category': 'completionist',
            'unlock_criteria': {'type': 'all_categories', 'value': 5}
        },
        {
            'name': 'Cinephile',
            'description': 'Shared 25 movies',
            'icon': '/badges/cinephile.png',
            'rarity': 'epic',
            'category': 'completionist',
            'unlock_criteria': {'type': 'shares_count', 'category': 'cinema', 'value': 25}
        },
        {
            'name': 'Audiophile',
            'description': 'Shared 25 albums',
            'icon': '/badges/audiophile.png',
            'rarity': 'epic',
            'category': 'completionist',
            'unlock_criteria': {'type': 'shares_count', 'category': 'music', 'value': 25}
        },
        {
            'name': 'Gaming Legend',
            'description': 'Shared 25 games',
            'icon': '/badges/gaming_legend.png',
            'rarity': 'epic',
            'category': 'completionist',
            'unlock_criteria': {'type': 'shares_count', 'category': 'games', 'value': 25}
        },
        {
            'name': 'Bookworm',
            'description': 'Shared 25 books',
            'icon': '/badges/bookworm.png',
            'rarity': 'epic',
            'category': 'completionist',
            'unlock_criteria': {'type': 'shares_count', 'category': 'books', 'value': 25}
        },
        {
            'name': 'World Explorer',
            'description': 'Shared 25 locations',
            'icon': '/badges/world_explorer.png',
            'rarity': 'epic',
            'category': 'completionist',
            'unlock_criteria': {'type': 'shares_count', 'category': 'travel', 'value': 25}
        },
        {
            'name': 'Ultimate Collector',
            'description': 'Shared 100 items total',
            'icon': '/badges/ultimate_collector.png',
            'rarity': 'legendary',
            'category': 'completionist',
            'unlock_criteria': {'type': 'shares_count', 'value': 100}
        },
        
        # Social badges - for community engagement
        {
            'name': 'Social Butterfly',
            'description': 'Created your first post',
            'icon': '/badges/social_butterfly.png',
            'rarity': 'common',
            'category': 'social',
            'unlock_criteria': {'type': 'posts_count', 'value': 1}
        },
        {
            'name': 'Conversationalist',
            'description': 'Made 10 posts',
            'icon': '/badges/conversationalist.png',
            'rarity': 'rare',
            'category': 'social',
            'unlock_criteria': {'type': 'posts_count', 'value': 10}
        },
        {
            'name': 'Community Favorite',
            'description': 'Earned 50 total likes',
            'icon': '/badges/community_favorite.png',
            'rarity': 'epic',
            'category': 'social',
            'unlock_criteria': {'type': 'total_likes', 'value': 50}
        },
        {
            'name': 'Influencer',
            'description': 'Earned 200 total likes',
            'icon': '/badges/influencer.png',
            'rarity': 'legendary',
            'category': 'social',
            'unlock_criteria': {'type': 'total_likes', 'value': 200}
        },
        
        # Streak badges - for consistent activity
        {
            'name': 'Consistent Creator',
            'description': 'Maintained a 7-day streak',
            'icon': '/badges/consistent_creator.png',
            'rarity': 'rare',
            'category': 'streak',
            'unlock_criteria': {'type': 'streak_days', 'value': 7}
        },
        {
            'name': 'Dedicated Curator',
            'description': 'Maintained a 30-day streak',
            'icon': '/badges/dedicated_curator.png',
            'rarity': 'epic',
            'category': 'streak',
            'unlock_criteria': {'type': 'streak_days', 'value': 30}
        },
        {
            'name': 'Eternal Flame',
            'description': 'Maintained a 100-day streak',
            'icon': '/badges/eternal_flame.png',
            'rarity': 'legendary',
            'category': 'streak',
            'unlock_criteria': {'type': 'streak_days', 'value': 100}
        },
        
        # Special badges - for unique achievements
        {
            'name': 'Taste Maker',
            'description': 'Reached curator level 5',
            'icon': '/badges/taste_maker.png',
            'rarity': 'epic',
            'category': 'special',
            'unlock_criteria': {'type': 'curator_level', 'value': 5}
        },
        {
            'name': 'Legendary Curator',
            'description': 'Reached curator level 10',
            'icon': '/badges/legendary_curator.png',
            'rarity': 'legendary',
            'category': 'special',
            'unlock_criteria': {'type': 'curator_level', 'value': 10}
        },
        {
            'name': 'Aura Master',
            'description': 'Perfected your aesthetic profile',
            'icon': '/badges/aura_master.png',
            'rarity': 'legendary',
            'category': 'special',
            'unlock_criteria': {'type': 'aura_complete', 'value': 1}
        },
    ]
    
    for badge_data in badges_data:
        # Check if badge already exists
        existing = db.query(Badge).filter_by(name=badge_data['name']).first()
        if existing:
            continue
        
        badge = Badge(**badge_data)
        db.add(badge)
    
    db.commit()
    print(f"✓ Seeded {len(badges_data)} badges")


def seed_curator_levels(db):
    """Create curator level progression system"""
    
    levels_data = [
        {
            'level': 1,
            'name': 'Novice Curator',
            'description': 'You\'ve started your curation journey',
            'xp_required': 0,
            'icon': '/levels/level_1.png'
        },
        {
            'level': 2,
            'name': 'Emerging Curator',
            'description': 'You\'re building your aesthetic identity',
            'xp_required': 100,
            'icon': '/levels/level_2.png'
        },
        {
            'level': 3,
            'name': 'Established Curator',
            'description': 'Your taste is becoming recognized',
            'xp_required': 300,
            'icon': '/levels/level_3.png'
        },
        {
            'level': 4,
            'name': 'Expert Curator',
            'description': 'You\'ve mastered the art of curation',
            'xp_required': 600,
            'icon': '/levels/level_4.png'
        },
        {
            'level': 5,
            'name': 'Master Curator',
            'description': 'A true connoisseur of aesthetics',
            'xp_required': 1000,
            'icon': '/levels/level_5.png'
        },
        {
            'level': 6,
            'name': 'Legendary Curator',
            'description': 'Your collections inspire others',
            'xp_required': 1500,
            'icon': '/levels/level_6.png'
        },
        {
            'level': 7,
            'name': 'Visionary Curator',
            'description': 'You set trends in the aesthetic community',
            'xp_required': 2200,
            'icon': '/levels/level_7.png'
        },
        {
            'level': 8,
            'name': 'Icon Curator',
            'description': 'A beacon of aesthetic excellence',
            'xp_required': 3000,
            'icon': '/levels/level_8.png'
        },
        {
            'level': 9,
            'name': 'Peak Curator',
            'description': 'Unparalleled taste and influence',
            'xp_required': 4000,
            'icon': '/levels/level_9.png'
        },
        {
            'level': 10,
            'name': 'Eternal Curator',
            'description': 'A legendary figure in the aesthetic realm',
            'xp_required': 5000,
            'icon': '/levels/level_10.png'
        },
    ]
    
    for level_data in levels_data:
        # Check if level already exists
        existing = db.query(CuratorLevel).filter_by(level=level_data['level']).first()
        if existing:
            continue
        
        level = CuratorLevel(**level_data)
        db.add(level)
    
    db.commit()
    print(f"✓ Seeded {len(levels_data)} curator levels")


def main():
    """Run the seed script"""
    app = create_app()
    
    with app.app_context():
        try:
            db = get_db()
            
            print("🌱 Seeding VibeCheck gamification data...")
            seed_badges(db)
            seed_curator_levels(db)
            
            print("✅ Database seeding complete!")
            return 0
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
