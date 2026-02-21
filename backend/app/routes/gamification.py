from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_db
from app.models.gamification import Badge, UserBadge, CuratorLevel, UserCuratorStats
from app.models.user import User
from app.services.badge_service import BadgeService

gamification_bp = Blueprint('gamification', __name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _seed_default_badges(db):
    """Seed default badges if database is empty"""
    badges_data = [
        # Early badges
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
        
        # Completionist badges
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
        
        # Social badges
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
        
        # Streak badges
        {
            'name': 'Consistent Creator',
            'description': 'Maintained a 7-day streak',
            'icon': '/badges/consistent_creator.png',
            'rarity': 'rare',
            'category': 'streak',
            'unlock_criteria': {'type': 'streak_days', 'value': 7}
        },
        {
            'name': 'Dedication Master',
            'description': 'Maintained a 30-day streak',
            'icon': '/badges/dedication_master.png',
            'rarity': 'epic',
            'category': 'streak',
            'unlock_criteria': {'type': 'streak_days', 'value': 30}
        },
        
        # Special badges
        {
            'name': 'Curator Elite',
            'description': 'Reached Level 5',
            'icon': '/badges/curator_elite.png',
            'rarity': 'legendary',
            'category': 'special',
            'unlock_criteria': {'type': 'curator_level', 'value': 5}
        },
    ]
    
    for badge_data in badges_data:
        badge = Badge(**badge_data)
        db.add(badge)
    
    db.commit()


# ============================================================================
# BADGES ENDPOINTS
# ============================================================================

@gamification_bp.route('/badges', methods=['GET'])
def get_badges():
    """
    Get all available badges with optional filtering
    ---
    tags:
      - Badges & Gamification
    parameters:
      - name: rarity
        in: query
        type: string
        description: Filter by badge rarity (common, uncommon, rare, legendary)
        required: false
      - name: category
        in: query
        type: string
        description: Filter by badge category (cinema, music, games, books, travel, curator, social)
        required: false
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
      - name: offset
        in: query
        type: integer
        default: 0
        description: Pagination offset
    responses:
      200:
        description: List of badges
        schema:
          type: object
          properties:
            badges:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                    example: b_123abc456def
                  name:
                    type: string
                    example: Cinephile
                  description:
                    type: string
                    example: Shared 5 movies
                  image:
                    type: string
                    example: /badges/cinephile.png
                  rarity:
                    type: string
                    example: common
                  category:
                    type: string
                    example: cinema
                  unlockedCount:
                    type: integer
                    example: 42
            total:
              type: integer
              example: 100
      400:
        description: Bad request - invalid parameters
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        db = get_db()
        
        # Auto-seed badges if none exist
        badge_count = db.query(Badge).count()
        if badge_count == 0:
            _seed_default_badges(db)
        
        # Parse query parameters
        rarity = request.args.get('rarity', None)
        category = request.args.get('category', None)
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Validate limit and offset
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
        
        # Build query
        query = db.query(Badge)
        
        if rarity:
            valid_rarities = ['common', 'rare', 'epic', 'legendary']
            if rarity not in valid_rarities:
                return jsonify({
                    'error': 'Bad Request',
                    'message': f'Invalid rarity. Must be one of: {", ".join(valid_rarities)}'
                }), 400
            query = query.filter_by(rarity=rarity)
        
        if category:
            valid_categories = ['early', 'completionist', 'social', 'streak', 'special']
            if category not in valid_categories:
                return jsonify({
                    'error': 'Bad Request',
                    'message': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
                }), 400
            query = query.filter_by(category=category)
        
        # Count total
        total = query.count()
        
        # Fetch paginated results
        badges = query.offset(offset).limit(limit).all()
        
        # Return direct list of badges as per OpenAPI spec
        return jsonify([badge.to_dict() for badge in badges]), 200
    
    except ValueError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': 'Invalid query parameters'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Server Error',
            'message': str(e)
        }), 500


@gamification_bp.route('/badges/user', methods=['GET'])
@jwt_required()
def get_user_badges():
    """
    Get current user's earned badges
    ---
    tags:
      - Badges & Gamification
    security:
      - Bearer: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
      - name: offset
        in: query
        type: integer
        default: 0
        description: Pagination offset
    responses:
      200:
        description: User's earned badges
        schema:
          type: object
          properties:
            badges:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  description:
                    type: string
                  image:
                    type: string
                  rarity:
                    type: string
                  category:
                    type: string
                  earnedAt:
                    type: string
                    format: date-time
            total:
              type: integer
      401:
        description: Unauthorized - missing or invalid authentication token
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        user_id = get_jwt_identity()
        db = get_db()
        
        # Parse query parameters
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
        
        # Fetch user badges
        query = db.query(UserBadge).filter_by(user_id=user_id)
        total_count = query.count()
        user_badges = query.offset(offset).limit(limit).all()
        
        # Format response - Return array of badges directly per OpenAPI spec
        badges_list = []
        for user_badge in user_badges:
            badge_dict = user_badge.badge.to_dict(user_badge=user_badge)
            badges_list.append(badge_dict)
        
        return jsonify(badges_list), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Server Error',
            'message': str(e)
        }), 500


@gamification_bp.route('/badges/user/<user_id>', methods=['GET'])
def get_user_badges_by_id(user_id):
    """
    Get specific user's earned badges
    ---
    tags:
      - Badges & Gamification
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
      - name: offset
        in: query
        type: integer
        default: 0
        description: Pagination offset
    responses:
      200:
        description: User's earned badges
        schema:
          type: object
          properties:
            badges:
              type: array
            total:
              type: integer
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        db = get_db()
        
        # Check if user exists
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': f'User with ID {user_id} not found'
            }), 404
        
        # Parse query parameters
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
        
        # Fetch user badges
        query = db.query(UserBadge).filter_by(user_id=user_id)
        total_count = query.count()
        user_badges = query.offset(offset).limit(limit).all()
        
        # Format response - Return array of badges directly per OpenAPI spec
        badges_list = []
        for user_badge in user_badges:
            badge_dict = user_badge.badge.to_dict(user_badge=user_badge)
            badges_list.append(badge_dict)
        
        return jsonify(badges_list), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Server Error',
            'message': str(e)
        }), 500


# ============================================================================
# CURATOR STATS ENDPOINTS
# ============================================================================

@gamification_bp.route('/curator/stats', methods=['GET'])
@jwt_required()
def get_curator_stats():
    """
    Get current user's curator statistics and progression
    ---
    tags:
      - Badges & Gamification
    security:
      - Bearer: []
    responses:
      200:
        description: User's curator statistics
        schema:
          type: object
          properties:
            userId:
              type: string
              example: u_123abc456def
            totalShares:
              type: integer
              example: 42
            currentXp:
              type: integer
              example: 750
            currentLevel:
              type: integer
              example: 3
            totalXp:
              type: integer
              example: 2500
            totalPosts:
              type: integer
              example: 18
            totalLikesReceived:
              type: integer
              example: 156
            totalCommentsReceived:
              type: integer
              example: 34
            contentDistribution:
              type: object
              properties:
                movies:
                  type: integer
                albums:
                  type: integer
                games:
                  type: integer
                books:
                  type: integer
                locations:
                  type: integer
            community:
              type: object
              properties:
                followersCount:
                  type: integer
                followingCount:
                  type: integer
                roomsJoined:
                  type: integer
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        user_id = get_jwt_identity()
        db = get_db()
        
        # Fetch or create curator stats
        stats = db.query(UserCuratorStats).filter_by(user_id=user_id).first()
        
        if not stats:
            # Create initial stats if not exists
            stats = UserCuratorStats(user_id=user_id)
            db.add(stats)
            db.commit()
        
        # Fetch user's badges for the badges array
        user_badges = db.query(UserBadge).filter_by(user_id=user_id).all()
        badges_list = [ub.badge.to_dict(user_badge=ub) for ub in user_badges]
        
        # Return UserStats schema as per OpenAPI spec
        return jsonify({
            'totalShares': stats.total_shares,
            'totalXP': stats.total_xp,
            'currentLevel': stats.current_level,
            'streakDays': stats.streak_days,
            'badges': badges_list,
            'completedFilmographies': [],  # TODO: Implement filmography tracking
            'finishedBooks': stats.finished_books,
            'earlyDiscoveries': stats.early_discoveries
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Server Error',
            'message': str(e)
        }), 500


@gamification_bp.route('/curator/stats/<user_id>', methods=['GET'])
def get_curator_stats_by_id(user_id):
    """
    Get specific user's curator statistics
    ---
    tags:
      - Badges & Gamification
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
    responses:
      200:
        description: User's curator statistics
        schema:
          type: object
          properties:
            userId:
              type: string
            totalShares:
              type: integer
            currentXp:
              type: integer
            currentLevel:
              type: integer
            totalXp:
              type: integer
            totalPosts:
              type: integer
            totalLikesReceived:
              type: integer
            totalCommentsReceived:
              type: integer
            contentDistribution:
              type: object
            community:
              type: object
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        db = get_db()
        
        # Check if user exists
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': f'User with ID {user_id} not found'
            }), 404
        
        # Fetch curator stats
        stats = db.query(UserCuratorStats).filter_by(user_id=user_id).first()
        
        if not stats:
            # Create initial stats if not exists
            stats = UserCuratorStats(user_id=user_id)
            db.add(stats)
            db.commit()
        
        # Fetch user's badges for the badges array
        user_badges = db.query(UserBadge).filter_by(user_id=user_id).all()
        badges_list = [ub.badge.to_dict(user_badge=ub) for ub in user_badges]
        
        # Return UserStats schema as per OpenAPI spec
        return jsonify({
            'totalShares': stats.total_shares,
            'totalXP': stats.total_xp,
            'currentLevel': stats.current_level,
            'streakDays': stats.streak_days,
            'badges': badges_list,
            'completedFilmographies': [],  # TODO: Implement filmography tracking
            'finishedBooks': stats.finished_books,
            'earlyDiscoveries': stats.early_discoveries
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Server Error',
            'message': str(e)
        }), 500


# ============================================================================
# CURATOR LEVELS ENDPOINTS
# ============================================================================

@gamification_bp.route('/curator/levels', methods=['GET'])
def get_curator_levels():
    """
    Get all curator levels in the progression system
    ---
    tags:
      - Badges & Gamification
    responses:
      200:
        description: List of all curator levels
        schema:
          type: object
          properties:
            levels:
              type: array
              items:
                type: object
                properties:
                  level:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: Novice Curator
                  description:
                    type: string
                    example: You've started your curation journey
                  xpRequired:
                    type: integer
                    example: 0
                  icon:
                    type: string
                    nullable: true
                    example: /levels/level_1.png
            total:
              type: integer
              example: 10
      400:
        description: Bad request
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        db = get_db()
        
        # Fetch all curator levels, ordered by level
        levels = db.query(CuratorLevel).order_by(CuratorLevel.level).all()
        
        # If no levels exist, create the default progression
        if not levels:
            default_levels = [
                {'level': 1, 'name': 'Novice Curator', 'description': "You've started your curation journey", 'xp_required': 0},
                {'level': 2, 'name': 'Emerging Curator', 'description': "You're building your aesthetic identity", 'xp_required': 100},
                {'level': 3, 'name': 'Established Curator', 'description': 'Your taste is becoming recognized', 'xp_required': 300},
                {'level': 4, 'name': 'Expert Curator', 'description': "You've mastered the art of curation", 'xp_required': 600},
                {'level': 5, 'name': 'Master Curator', 'description': 'A true connoisseur of aesthetics', 'xp_required': 1000},
                {'level': 6, 'name': 'Legendary Curator', 'description': 'Your collections inspire others', 'xp_required': 1500},
                {'level': 7, 'name': 'Visionary Curator', 'description': 'You set trends in the aesthetic community', 'xp_required': 2200},
                {'level': 8, 'name': 'Icon Curator', 'description': 'A beacon of aesthetic excellence', 'xp_required': 3000},
                {'level': 9, 'name': 'Peak Curator', 'description': 'Unparalleled taste and influence', 'xp_required': 4000},
                {'level': 10, 'name': 'Eternal Curator', 'description': 'A legendary figure in the aesthetic realm', 'xp_required': 5000},
            ]
            
            for level_data in default_levels:
                level = CuratorLevel(**level_data)
                db.add(level)
            
            db.commit()
            levels = db.query(CuratorLevel).order_by(CuratorLevel.level).all()
        
        # Return array of CuratorLevel objects directly as per OpenAPI spec
        return jsonify([level.to_dict() for level in levels]), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Server Error',
            'message': str(e)
        }), 500
