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
    
    badges_data = [
        # Cinema badges
        {
            'name': 'Cinephile',
            'description': 'Shared your first movie',
            'image': '/badges/cinephile.png',
            'rarity': 'common',
            'category': 'cinema',
            'unlock_criteria': {'type': 'shares_count', 'category': 'cinema', 'value': 1}
        },
        {
            'name': 'Film Buff',
            'description': 'Shared 10 movies',
            'image': '/badges/film_buff.png',
            'rarity': 'uncommon',
            'category': 'cinema',
            'unlock_criteria': {'type': 'shares_count', 'category': 'cinema', 'value': 10}
        },
        {
            'name': 'Director\'s Favorite',
            'description': 'Earned 50 likes on movie shares',
            'image': '/badges/directors_favorite.png',
            'rarity': 'rare',
            'category': 'cinema',
            'unlock_criteria': {'type': 'likes_on_category', 'category': 'cinema', 'value': 50}
        },
        
        # Music badges
        {
            'name': 'Melody Lover',
            'description': 'Shared your first album',
            'image': '/badges/melody_lover.png',
            'rarity': 'common',
            'category': 'music',
            'unlock_criteria': {'type': 'shares_count', 'category': 'music', 'value': 1}
        },
        {
            'name': 'Audiophile',
            'description': 'Shared 10 albums',
            'image': '/badges/audiophile.png',
            'rarity': 'uncommon',
            'category': 'music',
            'unlock_criteria': {'type': 'shares_count', 'category': 'music', 'value': 10}
        },
        {
            'name': 'Music Curator',
            'description': 'Earned 50 likes on music shares',
            'image': '/badges/music_curator.png',
            'rarity': 'rare',
            'category': 'music',
            'unlock_criteria': {'type': 'likes_on_category', 'category': 'music', 'value': 50}
        },
        
        # Games badges
        {
            'name': 'Game Enthusiast',
            'description': 'Shared your first game',
            'image': '/badges/game_enthusiast.png',
            'rarity': 'common',
            'category': 'games',
            'unlock_criteria': {'type': 'shares_count', 'category': 'games', 'value': 1}
        },
        {
            'name': 'Gamer',
            'description': 'Shared 10 games',
            'image': '/badges/gamer.png',
            'rarity': 'uncommon',
            'category': 'games',
            'unlock_criteria': {'type': 'shares_count', 'category': 'games', 'value': 10}
        },
        {
            'name': 'Gaming Expert',
            'description': 'Earned 75 likes on game shares',
            'image': '/badges/gaming_expert.png',
            'rarity': 'legendary',
            'category': 'games',
            'unlock_criteria': {'type': 'likes_on_category', 'category': 'games', 'value': 75}
        },
        
        # Books badges
        {
            'name': 'Bookworm',
            'description': 'Shared your first book',
            'image': '/badges/bookworm.png',
            'rarity': 'common',
            'category': 'books',
            'unlock_criteria': {'type': 'shares_count', 'category': 'books', 'value': 1}
        },
        {
            'name': 'Reader',
            'description': 'Shared 10 books',
            'image': '/badges/reader.png',
            'rarity': 'uncommon',
            'category': 'books',
            'unlock_criteria': {'type': 'shares_count', 'category': 'books', 'value': 10}
        },
        {
            'name': 'Literary Critic',
            'description': 'Earned 60 likes on book shares',
            'image': '/badges/literary_critic.png',
            'rarity': 'rare',
            'category': 'books',
            'unlock_criteria': {'type': 'likes_on_category', 'category': 'books', 'value': 60}
        },
        
        # Travel badges
        {
            'name': 'Explorer',
            'description': 'Shared your first travel destination',
            'image': '/badges/explorer.png',
            'rarity': 'common',
            'category': 'travel',
            'unlock_criteria': {'type': 'shares_count', 'category': 'travel', 'value': 1}
        },
        {
            'name': 'Wanderer',
            'description': 'Shared 10 travel destinations',
            'image': '/badges/wanderer.png',
            'rarity': 'uncommon',
            'category': 'travel',
            'unlock_criteria': {'type': 'shares_count', 'category': 'travel', 'value': 10}
        },
        {
            'name': 'World Traveler',
            'description': 'Earned 100 likes on travel shares',
            'image': '/badges/world_traveler.png',
            'rarity': 'legendary',
            'category': 'travel',
            'unlock_criteria': {'type': 'likes_on_category', 'category': 'travel', 'value': 100}
        },
        
        # Curator badges
        {
            'name': 'Rising Curator',
            'description': 'Reached curator level 2',
            'image': '/badges/rising_curator.png',
            'rarity': 'uncommon',
            'category': 'curator',
            'unlock_criteria': {'type': 'curator_level', 'value': 2}
        },
        {
            'name': 'Established Curator',
            'description': 'Reached curator level 5',
            'image': '/badges/established_curator.png',
            'rarity': 'rare',
            'category': 'curator',
            'unlock_criteria': {'type': 'curator_level', 'value': 5}
        },
        {
            'name': 'Master Curator',
            'description': 'Reached curator level 10',
            'image': '/badges/master_curator.png',
            'rarity': 'legendary',
            'category': 'curator',
            'unlock_criteria': {'type': 'curator_level', 'value': 10}
        },
        
        # Social badges
        {
            'name': 'Social Butterfly',
            'description': 'Created your first post',
            'image': '/badges/social_butterfly.png',
            'rarity': 'common',
            'category': 'social',
            'unlock_criteria': {'type': 'posts_count', 'value': 1}
        },
        {
            'name': 'Community Member',
            'description': 'Earned 50 total likes',
            'image': '/badges/community_member.png',
            'rarity': 'uncommon',
            'category': 'social',
            'unlock_criteria': {'type': 'total_likes', 'value': 50}
        },
        {
            'name': 'Influencer',
            'description': 'Earned 500 total likes',
            'image': '/badges/influencer.png',
            'rarity': 'legendary',
            'category': 'social',
            'unlock_criteria': {'type': 'total_likes', 'value': 500}
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
