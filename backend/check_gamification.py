"""
Utility script to check gamification data in the database
Run this to see what badges and levels are currently in your database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import get_db
from app.models.gamification import Badge, CuratorLevel


def check_gamification_data():
    """Check what gamification data exists in the database"""
    app = create_app()
    
    with app.app_context():
        try:
            db = get_db()
            
            print("\n" + "="*60)
            print("🔍 VIBECHECK GAMIFICATION DATABASE CHECK")
            print("="*60 + "\n")
            
            # Check badges
            badges = db.query(Badge).order_by(Badge.category, Badge.rarity).all()
            badge_count = len(badges)
            
            print(f"📛 BADGES: {badge_count} total\n")
            
            if badge_count == 0:
                print("   ⚠️  No badges found in database!")
                print("   Run 'python seed_gamification.py' to seed badges\n")
            else:
                # Group by category
                categories = {}
                for badge in badges:
                    if badge.category not in categories:
                        categories[badge.category] = []
                    categories[badge.category].append(badge)
                
                for category, badges_in_cat in sorted(categories.items()):
                    print(f"   {category.upper()}: {len(badges_in_cat)} badges")
                    for badge in badges_in_cat:
                        rarity_emoji = {
                            'common': '⚪',
                            'rare': '🔵', 
                            'epic': '🟣',
                            'legendary': '🟡'
                        }.get(badge.rarity, '⚪')
                        print(f"      {rarity_emoji} {badge.name} ({badge.rarity})")
                        print(f"         {badge.description}")
                    print()
            
            # Check curator levels
            levels = db.query(CuratorLevel).order_by(CuratorLevel.level).all()
            level_count = len(levels)
            
            print(f"📊 CURATOR LEVELS: {level_count} total\n")
            
            if level_count == 0:
                print("   ⚠️  No curator levels found in database!")
                print("   Run 'python seed_gamification.py' to seed levels\n")
            else:
                for level in levels:
                    print(f"   Level {level.level}: {level.name} ({level.xp_required} XP)")
                    print(f"      {level.description}")
                print()
            
            # Summary
            print("="*60)
            print("📈 SUMMARY")
            print("="*60)
            print(f"   Total Badges: {badge_count}")
            print(f"   Total Levels: {level_count}")
            
            if badge_count > 0 or level_count > 0:
                print("\n✅ Gamification data is populated!")
            else:
                print("\n⚠️  Gamification data is EMPTY!")
                print("   Run: python seed_gamification.py")
            
            print()
            
            return 0
            
        except Exception as e:
            print(f"\n❌ Error checking database: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(check_gamification_data())
