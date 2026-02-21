"""
Badge unlock service for VibeCheck
Handles badge unlock logic and checking when users perform various actions
"""
from app.database import get_db
from app.models.gamification import Badge, UserBadge
from app.models.share import Share
from app.models.post import Post, PostLike
from app.seed_gamification import seed_badges, seed_curator_levels
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Any


class BadgeService:
    """Service for managing badge unlocks and checking criteria"""
    
    @staticmethod
    def check_and_unlock_badges(user_id: str) -> List[str]:
        """
        Check all badges and unlock any that the user now qualifies for
        Returns list of newly unlocked badge IDs
        
        Args:
            user_id: The user ID to check badges for
            
        Returns:
            List of newly unlocked badge IDs
        """
        db = get_db()
        newly_unlocked = []
        
        try:
            # Auto-seed badges if none exist
            badge_count = db.query(Badge).count()
            if badge_count == 0:
                print(f"🌱 [BadgeService] Auto-seeding default badges...")
                seed_badges(db)
                seed_curator_levels(db)
                print(f"✓ [BadgeService] Badges seeded successfully (count: {db.query(Badge).count()})")
            
            # Get all badges that aren't already unlocked by this user
            unlocked_badge_ids = db.query(UserBadge.badge_id).filter_by(
                user_id=user_id
            ).all()
            unlocked_badge_ids = [b[0] for b in unlocked_badge_ids]
            
            # Get all available badges
            all_badges = db.query(Badge).all()
            print(f"Checking {len(all_badges)} badges for user {user_id} (already has {len(unlocked_badge_ids)})")
            
            for badge in all_badges:
                # Skip if already unlocked
                if badge.id in unlocked_badge_ids:
                    continue
                
                # Check if criteria are met
                if BadgeService._check_badge_criteria(badge, user_id, db):
                    # Create UserBadge record
                    user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
                    db.add(user_badge)
                    newly_unlocked.append(badge.id)
                    print(f"🎉 Unlocked badge: {badge.name} (ID: {badge.id})")
            
            if newly_unlocked:
                db.commit()
                print(f"✓ Committed {len(newly_unlocked)} new badges")
            
            return newly_unlocked
        
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def _check_badge_criteria(badge: Badge, user_id: str, db: Any) -> bool:
        """
        Check if a user meets the criteria for a specific badge
        
        Args:
            badge: The badge to check criteria for
            user_id: The user ID to check
            db: Database session
            
        Returns:
            True if criteria are met, False otherwise
        """
        if badge.unlock_criteria is None:
            return False
        
        criteria = badge.unlock_criteria
        criteria_type = criteria.get('type')
        
        # Check total shares count (all categories)
        if criteria_type == 'shares_count' and 'category' not in criteria:
            value = criteria.get('value', 0)
            
            count = db.query(func.count(Share.id)).filter(
                Share.user_id == user_id
            ).scalar()
            
            print(f"  Badge '{badge.name}': checking shares_count {count} >= {value}")
            return count >= value
        
        # Check shares count by specific category
        elif criteria_type == 'shares_count' and 'category' in criteria:
            category = criteria.get('category')
            value = criteria.get('value', 0)
            
            count = db.query(func.count(Share.id)).filter(
                Share.user_id == user_id,
                Share.category == category
            ).scalar()
            
            return count >= value
        
        # Check if user has shared from all categories
        elif criteria_type == 'all_categories':
            required_count = criteria.get('value', 5)
            
            distinct_categories = db.query(func.count(func.distinct(Share.category))).filter(
                Share.user_id == user_id
            ).scalar()
            
            return distinct_categories >= required_count
        
        # Check likes on category shares
        elif criteria_type == 'likes_on_category':
            category = criteria.get('category')
            value = criteria.get('value', 0)
            
            # Get user's posts in this category
            user_posts = db.query(Post.id).filter(
                Post.user_id == user_id,
                Post.category == category
            ).all()
            post_ids = [p[0] for p in user_posts]
            
            if len(post_ids) == 0:
                return False
            
            # Count likes on these posts
            likes_count = db.query(func.count(PostLike.id)).filter(
                PostLike.post_id.in_(post_ids)
            ).scalar()
            
            return likes_count >= value
        
        # Check total likes across all posts
        elif criteria_type == 'total_likes':
            value = criteria.get('value', 0)
            
            # Get all user's posts
            user_posts = db.query(Post.id).filter_by(user_id=user_id).all()
            post_ids = [p[0] for p in user_posts]
            
            if len(post_ids) == 0:
                return False
            
            # Count likes on all posts
            likes_count = db.query(func.count(PostLike.id)).filter(
                PostLike.post_id.in_(post_ids)
            ).scalar()
            
            return likes_count >= value
        
        # Check number of posts created
        elif criteria_type == 'posts_count':
            value = criteria.get('value', 0)
            
            count = db.query(func.count(Post.id)).filter(
                Post.user_id == user_id
            ).scalar()
            
            return count >= value
        
        # Check streak days
        elif criteria_type == 'streak_days':
            value = criteria.get('value', 0)
            
            try:
                from app.models.gamification import UserCuratorStats
                stats = db.query(UserCuratorStats).filter_by(user_id=user_id).first()
                if stats is None:
                    return False
                
                return stats.streak_days >= value
            except (AttributeError, Exception):
                return False
        
        # Check curator level reached
        elif criteria_type == 'curator_level':
            value = criteria.get('value', 1)
            
            try:
                from app.models.gamification import UserCuratorStats
                stats = db.query(UserCuratorStats).filter_by(user_id=user_id).first()
                if stats is None:
                    return False
                
                return stats.current_level >= value
            except (AttributeError, Exception):
                return False
        
        # Check early user (for special early adopter badge)
        elif criteria_type == 'early_user':
            # Check if user_id is among first N users
            value = criteria.get('value', 1000)
            
            try:
                from app.models.user import User
                # Count users created before this user
                user = db.query(User).filter_by(user_id=user_id).first()
                if user is None:
                    return False
                
                earlier_users = db.query(func.count(User.user_id)).filter(
                    User.created_at < user.created_at
                ).scalar()
                
                return earlier_users < value
            except (AttributeError, Exception):
                return False
        
        # Check aura profile completion
        elif criteria_type == 'aura_complete':
            try:
                from app.models.user import User
                user = db.query(User).filter_by(user_id=user_id).first()
                if user is None:
                    return False
                
                # Check if user has aesthetic tags and aura colors set
                has_tags = user.aesthetic_tags and len(user.aesthetic_tags) >= 3
                has_colors = user.aura_colors and len(user.aura_colors) >= 2
                has_bio = user.bio and len(user.bio) > 20
                has_avatar = user.avatar is not None
                
                return has_tags and has_colors and has_bio and has_avatar
            except (AttributeError, Exception):
                return False
        
        return False
    
    @staticmethod
    def get_user_unlocked_badges(user_id: str) -> List[dict]:
        """
        Get all badges unlocked by a user with details
        
        Args:
            user_id: The user ID
            
        Returns:
            List of badge dictionaries with unlock info
        """
        db = get_db()
        
        user_badges = db.query(UserBadge).filter_by(user_id=user_id).all()
        
        result = []
        for user_badge in user_badges:
            # Pass user_badge to to_dict for proper formatting
            badge_data = user_badge.badge.to_dict(user_badge=user_badge)
            result.append(badge_data)
        
        return result
    
    @staticmethod
    def get_badge_progress(user_id: str) -> dict:
        """
        Get badge unlock progress for a user (for display purposes)
        Shows progress toward unlocking badges
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary with badge progress info
        """
        db = get_db()
        
        try:
            # Get unlocked badges
            unlocked = db.query(UserBadge).filter_by(user_id=user_id).count()
            total = db.query(Badge).count()
            
            # Get user stats for progress calculations
            from app.models.user import User
            user = db.query(User).filter_by(user_id=user_id).first()
            
            if user is None:
                return {'unlocked': 0, 'total': total, 'progress': 0, 'nextBadges': []}
            
            # Calculate progress toward next badges
            all_badges = db.query(Badge).all()
            unlocked_badge_ids = db.query(UserBadge.badge_id).filter_by(
                user_id=user_id
            ).all()
            unlocked_badge_ids = set(b[0] for b in unlocked_badge_ids)
            
            next_badges = []
            for badge in all_badges:
                if badge.id not in unlocked_badge_ids:
                    progress_info = BadgeService._calculate_badge_progress(
                        badge, user_id, db, user
                    )
                    if progress_info is not None:
                        next_badges.append(progress_info)
            
            # Sort by progress and take top 5
            next_badges.sort(key=lambda x: x.get('progress', 0), reverse=True)
            next_badges = next_badges[:5]
            
            return {
                'unlocked': unlocked,
                'total': total,
                'progress': round((unlocked / total * 100), 1) if total > 0 else 0,
                'nextBadges': next_badges
            }
        
        except Exception as e:
            return {'unlocked': 0, 'total': 0, 'progress': 0, 'nextBadges': []}
    
    @staticmethod
    def _calculate_badge_progress(badge: Badge, user_id: str, db: Any, user: Any) -> Optional[dict]:
        """
        Calculate progress toward unlocking a specific badge
        Returns progress percentage and current/required values
        """
        if badge.unlock_criteria is None:
            return None
        
        criteria = badge.unlock_criteria
        criteria_type = criteria.get('type')
        
        progress_info = {
            'badgeId': badge.id,
            'name': badge.name,
            'description': badge.description,
            'progress': 0,
            'current': 0,
            'required': 0
        }
        
        try:
            # Shares count by category
            if criteria_type == 'shares_count':
                category = criteria.get('category')
                required = criteria.get('value', 0)
                
                current = db.query(func.count(Share.id)).filter(
                    Share.user_id == user_id,
                    Share.category == category
                ).scalar()
                
                progress_info['current'] = current
                progress_info['required'] = required
                progress_info['progress'] = min(100, round((current / required * 100), 0)) if required > 0 else 0
            
            # Likes on category
            elif criteria_type == 'likes_on_category':
                category = criteria.get('category')
                required = criteria.get('value', 0)
                
                user_posts = db.query(Post.id).filter(
                    Post.user_id == user_id,
                    Post.category == category
                ).all()
                post_ids = [p[0] for p in user_posts]
                
                current = 0
                if len(post_ids) > 0:
                    current = db.query(func.count(PostLike.id)).filter(
                        PostLike.post_id.in_(post_ids)
                    ).scalar()
                
                progress_info['current'] = current
                progress_info['required'] = required
                progress_info['progress'] = min(100, round((current / required * 100), 0)) if required > 0 else 0
            
            # Total likes
            elif criteria_type == 'total_likes':
                required = criteria.get('value', 0)
                
                user_posts = db.query(Post.id).filter_by(user_id=user_id).all()
                post_ids = [p[0] for p in user_posts]
                
                current = 0
                if len(post_ids) > 0:
                    current = db.query(func.count(PostLike.id)).filter(
                        PostLike.post_id.in_(post_ids)
                    ).scalar()
                
                progress_info['current'] = current
                progress_info['required'] = required
                progress_info['progress'] = min(100, round((current / required * 100), 0)) if required > 0 else 0
            
            # Posts count
            elif criteria_type == 'posts_count':
                required = criteria.get('value', 0)
                
                current = db.query(func.count(Post.id)).filter(
                    Post.user_id == user_id
                ).scalar()
                
                progress_info['current'] = current
                progress_info['required'] = required
                progress_info['progress'] = min(100, round((current / required * 100), 0)) if required > 0 else 0
            
            # Curator level
            elif criteria_type == 'curator_level':
                required = criteria.get('value', 1)
                try:
                    curator_stats = getattr(user, 'curator_stats', None)
                    current = curator_stats.current_level if curator_stats is not None else 0
                except (AttributeError, Exception):
                    current = 0
                
                progress_info['current'] = current
                progress_info['required'] = required
                progress_info['progress'] = min(100, round((current / required * 100), 0)) if required > 0 else 0
            
            return progress_info
        
        except:
            return None
