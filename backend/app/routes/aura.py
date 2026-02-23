from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.share import Share
from app.models.gamification import UserCuratorStats
from app.services.badge_service import BadgeService
from typing import cast, List, Optional

aura_bp = Blueprint('aura', __name__)


# ──────────────────────────────────────────────
# AURA PROFILE ENDPOINTS
# ──────────────────────────────────────────────

@aura_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_current_user_aura():
    """
    Get current user's aura profile
    ---
    tags:
      - Aura
    security:
      - Bearer: []
    responses:
      200:
        description: Aura profile retrieved
        schema:
          type: object
          properties:
            userId:
              type: string
            username:
              type: string
            avatar:
              type: string
            bio:
              type: string
            recentShares:
              type: array
            auraColors:
              type: array
            aestheticTags:
              type: array
            topCategories:
              type: array
      401:
        description: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        # Get user
        user = db.query(User).filter_by(user_id=current_user_id).first()
        
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404
        
        # Get recent shares (limit 10)
        recent_shares = db.query(Share).filter_by(
            user_id=current_user_id
        ).order_by(Share.created_at.desc()).limit(10).all()
        
        # Calculate category distribution
        category_counts = db.query(
            Share.category,
            func.count(Share.id).label('count')
        ).filter_by(user_id=current_user_id).group_by(Share.category).all()
        
        total_shares: int = sum([cast(int, c.count) for c in category_counts], 0)
        top_categories = []
        
        if total_shares > 0:
            for cat in category_counts:
                percentage = round((cast(int, cat.count) / total_shares) * 100, 1)
                top_categories.append({
                    'category': cat.category,
                    'percentage': percentage
                })
            # Sort by percentage descending
            top_categories.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Build aura profile response
        aura_profile = {
            'userId': user.user_id,
            'username': user.username,
            'avatar': user.avatar,
            'bio': user.bio,
            'recentShares': [share.to_dict() for share in recent_shares],
            'auraColors': user.aura_colors or [],
            'aestheticTags': user.aesthetic_tags or [],
            'topCategories': top_categories
        }
        
        return jsonify(aura_profile), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@aura_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_aura_profile():
    """
    Update aura profile
    ---
    tags:
      - Aura
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        description: Aura profile fields to update
        required: true
        schema:
          type: object
          properties:
            aestheticTags:
              type: array
              items:
                type: string
            auraColors:
              type: array
              items:
                type: string
                pattern: '^#[0-9A-Fa-f]{6}$'
    responses:
      200:
        description: Aura profile updated
      400:
        description: Bad request - validation error
      401:
        description: Unauthorized
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        db = get_db()
        
        # Get user
        user = db.query(User).filter_by(user_id=current_user_id).first()
        
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404
        
        # aesthetic_tags are computed automatically by the aura inference
        # service and must not be set manually.
        if 'aestheticTags' in data:
            return jsonify({
                'error': 'Forbidden',
                'message': 'aestheticTags are computed automatically and cannot be set manually'
            }), 403
        
        # Update aura colors
        if 'auraColors' in data:
            if not isinstance(data['auraColors'], list):
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'auraColors must be an array'
                }), 400
            
            # Validate hex color format
            import re
            hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
            for color in data['auraColors']:
                if not hex_pattern.match(color):
                    return jsonify({
                        'error': 'Bad Request',
                        'message': f'Invalid color format: {color}. Must be #RRGGBB'
                    }), 400
            
            user.aura_colors = data['auraColors']
        
        db.commit()
        
        # Return full aura profile
        # Get recent shares
        recent_shares = db.query(Share).filter_by(
            user_id=current_user_id
        ).order_by(Share.created_at.desc()).limit(10).all()
        
        # Calculate category distribution
        category_counts = db.query(
            Share.category,
            func.count(Share.id).label('count')
        ).filter_by(user_id=current_user_id).group_by(Share.category).all()
        
        total_shares: int = sum([cast(int, c.count) for c in category_counts], 0)
        top_categories = []
        
        if total_shares > 0:
            for cat in category_counts:
                percentage = round((cast(int, cat.count) / total_shares) * 100, 1)
                top_categories.append({
                    'category': cat.category,
                    'percentage': percentage
                })
            top_categories.sort(key=lambda x: x['percentage'], reverse=True)
        
        aura_profile = {
            'userId': user.user_id,
            'username': user.username,
            'avatar': user.avatar,
            'bio': user.bio,
            'recentShares': [share.to_dict() for share in recent_shares],
            'auraColors': user.aura_colors or [],
            'aestheticTags': user.aesthetic_tags or [],
            'topCategories': top_categories
        }
        
        return jsonify(aura_profile), 200
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@aura_bp.route('/profile/<string:user_id>', methods=['GET'])
def get_user_aura(user_id):
    """
    Get user's aura profile by ID (public endpoint)
    ---
    tags:
      - Aura
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
    responses:
      200:
        description: Aura profile retrieved
      404:
        description: User not found
    """
    try:
        db = get_db()
        
        # Get user
        user = db.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404
        
        # Get recent shares
        recent_shares = db.query(Share).filter_by(
            user_id=user_id
        ).order_by(Share.created_at.desc()).limit(10).all()
        
        # Calculate category distribution
        category_counts = db.query(
            Share.category,
            func.count(Share.id).label('count')
        ).filter_by(user_id=user_id).group_by(Share.category).all()
        
        total_shares: int = sum([cast(int, c.count) for c in category_counts], 0)
        top_categories = []
        
        if total_shares > 0:
            for cat in category_counts:
                percentage = round((cast(int, cat.count) / total_shares) * 100, 1)
                top_categories.append({
                    'category': cat.category,
                    'percentage': percentage
                })
            top_categories.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Build aura profile response
        aura_profile = {
            'userId': user.user_id,
            'username': user.username,
            'avatar': user.avatar,
            'bio': user.bio,
            'recentShares': [share.to_dict() for share in recent_shares],
            'auraColors': user.aura_colors or [],
            'aestheticTags': user.aesthetic_tags or [],
            'topCategories': top_categories
        }
        
        return jsonify(aura_profile), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


# ──────────────────────────────────────────────
# SHARES ENDPOINTS
# ──────────────────────────────────────────────

@aura_bp.route('/shares', methods=['GET'])
@jwt_required()
def get_user_shares():
    """
    Get current user's shares with pagination
    ---
    tags:
      - Shares
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
        description: User shares list
        schema:
          type: object
          properties:
            total:
              type: integer
            limit:
              type: integer
            offset:
              type: integer
            data:
              type: array
      401:
        description: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        # Pagination parameters
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate pagination
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
        
        # Query shares
        query = db.query(Share).filter_by(user_id=current_user_id)
        total = query.count()
        
        shares = query.order_by(
            Share.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return jsonify({
            'total': total,
            'limit': limit,
            'offset': offset,
            'data': [share.to_dict() for share in shares]
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@aura_bp.route('/shares', methods=['POST'])
@jwt_required()
def create_share():
    """
    Create a new share
    ---
    tags:
      - Shares
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        description: Share data
        required: true
        schema:
          type: object
          required:
            - category
            - contentId
          properties:
            category:
              type: string
              enum: [cinema, music, games, books, travel]
            contentId:
              type: string
            caption:
              type: string
              maxLength: 500
    responses:
      201:
        description: Share created
        schema:
          type: object
      400:
        description: Bad request - validation error
      401:
        description: Unauthorized
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        # Validate required fields
        if 'category' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'category is required'
            }), 400
        
        if 'contentId' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'contentId is required'
            }), 400
        
        # Validate category
        valid_categories = ['cinema', 'music', 'games', 'books', 'travel']
        if data['category'] not in valid_categories:
            return jsonify({
                'error': 'Bad Request',
                'message': f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            }), 400
        
        # Validate caption length if provided
        caption = data.get('caption')
        if caption and len(caption) > 500:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Caption must be 500 characters or less'
            }), 400
        
        db = get_db()
        
        # Verify user exists
        user = db.query(User).filter_by(user_id=current_user_id).first()
        if not user:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'User not found'
            }), 401
        
        # For now, we'll use the contentId as the title
        # In a real implementation, you'd fetch the actual title from the external API
        title = data.get('title', f"{data['category'].title()} - {data['contentId']}")
        
        # Create new share
        new_share = Share(
            user_id=current_user_id,
            category=data['category'],
            content_id=data['contentId'],
            title=title,
            image=data.get('image'),
            dominant_color=data.get('dominantColor'),
            caption=caption
        )
        
        db.add(new_share)
        db.commit()
        db.refresh(new_share)
        
        # Update user curator stats
        try:
            stats = db.query(UserCuratorStats).filter_by(user_id=current_user_id).first()
            if not stats:
                # Create new stats if they don't exist
                stats = UserCuratorStats(user_id=current_user_id)
                db.add(stats)
            
            # Increment total shares
            stats.total_shares += 1  # type: ignore
            
            # Increment category-specific count
            category = data['category']
            if category == 'cinema':
                stats.movies_count += 1  # type: ignore
            elif category == 'music':
                stats.albums_count += 1  # type: ignore
            elif category == 'games':
                stats.games_count += 1  # type: ignore
            elif category == 'books':
                stats.books_count += 1  # type: ignore
            elif category == 'travel':
                stats.locations_count += 1  # type: ignore
            
            # Award XP for sharing (e.g., 10 XP per share)
            stats.total_xp += 10  # type: ignore
            stats.current_xp += 10  # type: ignore
            
            # Check for level up
            from app.models.gamification import CuratorLevel
            next_level = db.query(CuratorLevel).filter(
                CuratorLevel.level == stats.current_level + 1
            ).first()
            
            if next_level is not None and stats.total_xp >= next_level.xp_required:  # type: ignore
                stats.current_level = next_level.level  # type: ignore
                stats.current_xp = stats.total_xp - next_level.xp_required  # type: ignore
            
            db.commit()
        except Exception as stats_error:
            # Don't fail the request if stats update fails
            print(f"Stats update error: {stats_error}")
        
        # Check and unlock badges
        try:
            newly_unlocked = BadgeService.check_and_unlock_badges(current_user_id)
            if newly_unlocked:
                print(f"✓ Unlocked badges: {newly_unlocked}")
        except Exception as badge_error:
            # Don't fail the request if badge checking fails
            print(f"❌ Badge unlock error: {badge_error}")
            import traceback
            traceback.print_exc()

        # Recompute aura profile (colors + tags) from latest activity
        try:
            from app.services.aura_inference import infer_aura_for_user
            infer_aura_for_user(db, current_user_id)
        except Exception as aura_error:
            print(f"Aura inference error: {aura_error}")

        return jsonify(new_share.to_dict()), 201
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


# ──────────────────────────────────────────────
# AURA MATCHING ENDPOINTS
# ──────────────────────────────────────────────

@aura_bp.route('/matches', methods=['GET'])
@jwt_required()
def get_aura_matches():
    """
    Get aura matches (similar users based on aesthetic preferences)
    ---
    tags:
      - Aura
    security:
      - Bearer: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 10
        minimum: 1
        maximum: 50
        description: Maximum number of matches to return
      - name: offset
        in: query
        type: integer
        default: 0
        minimum: 0
        description: Number of results to skip for pagination
    responses:
      200:
        description: List of aura matches
        schema:
          type: object
          properties:
            data:
              type: array
            total:
              type: integer
      401:
        description: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        # Pagination parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate pagination
        if limit < 1 or limit > 50:
            limit = 10
        if offset < 0:
            offset = 0
        
        # Get current user
        current_user = db.query(User).filter_by(user_id=current_user_id).first()
        if not current_user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404
        
        # Get current user's shares and category distribution
        current_shares = db.query(Share).filter_by(user_id=current_user_id).all()
        current_category_counts = {}
        for share in current_shares:
            current_category_counts[share.category] = current_category_counts.get(share.category, 0) + 1
        
        current_total_shares = len(current_shares)
        # Get aesthetic tags and colors (JSON columns return list or None)
        cur_tags = cast(Optional[List[str]], current_user.aesthetic_tags)
        cur_colors = cast(Optional[List[str]], current_user.aura_colors)
        current_aesthetic_tags = set(cur_tags if cur_tags is not None else [])
        current_aura_colors = set(cur_colors if cur_colors is not None else [])
        
        # Get all other users
        other_users = db.query(User).filter(User.user_id != current_user_id).all()
        
        matches = []
        
        for user in other_users:
            # Calculate similarity score
            similarity_score = 0
            shared_aesthetics = []
            match_reasons = []
            
            # 1. Compare aesthetic tags (40% weight)
            usr_tags = cast(Optional[List[str]], user.aesthetic_tags)
            user_aesthetic_tags = set(usr_tags if usr_tags is not None else [])
            if current_aesthetic_tags and user_aesthetic_tags:
                shared_tags = current_aesthetic_tags.intersection(user_aesthetic_tags)
                if shared_tags:
                    tag_similarity = (len(shared_tags) / len(current_aesthetic_tags.union(user_aesthetic_tags))) * 100
                    similarity_score += tag_similarity * 0.4
                    shared_aesthetics.extend(list(shared_tags))
                    if len(shared_tags) > 0:
                        tags_str = ', '.join(list(shared_tags)[:3])
                        match_reasons.append(f"You both vibe with {tags_str}")
            
            # 2. Compare aura colors (20% weight)
            usr_colors = cast(Optional[List[str]], user.aura_colors)
            user_aura_colors = set(usr_colors if usr_colors is not None else [])
            if current_aura_colors and user_aura_colors:
                shared_colors = current_aura_colors.intersection(user_aura_colors)
                if shared_colors:
                    color_similarity = (len(shared_colors) / len(current_aura_colors.union(user_aura_colors))) * 100
                    similarity_score += color_similarity * 0.2
            
            # 3. Compare category preferences (40% weight)
            user_shares = db.query(Share).filter_by(user_id=user.user_id).all()
            user_category_counts = {}
            for share in user_shares:
                user_category_counts[share.category] = user_category_counts.get(share.category, 0) + 1
            
            user_total_shares = len(user_shares)
            
            if current_total_shares > 0 and user_total_shares > 0:
                # Calculate category distribution similarity
                all_categories = set(current_category_counts.keys()).union(set(user_category_counts.keys()))
                category_similarity = 0
                shared_categories = []
                
                for category in all_categories:
                    current_pct = (current_category_counts.get(category, 0) / current_total_shares) * 100
                    user_pct = (user_category_counts.get(category, 0) / user_total_shares) * 100
                    
                    # Calculate similarity for this category (inverse of difference)
                    category_diff = abs(current_pct - user_pct)
                    category_sim = max(0, 100 - category_diff)
                    category_similarity += category_sim
                    
                    # Track shared interests
                    if current_pct > 0 and user_pct > 0:
                        shared_categories.append(category)
                
                if len(all_categories) > 0:
                    category_similarity = category_similarity / len(all_categories)
                    similarity_score += category_similarity * 0.4
                    
                    if shared_categories:
                        shared_aesthetics.extend(shared_categories)
                        cats_str = ', '.join(shared_categories[:3])
                        match_reasons.append(f"You both enjoy {cats_str}")
            
            # Round similarity score
            similarity_score = min(100, max(0, round(similarity_score)))
            
            # Only include matches with similarity > 0
            if similarity_score > 0:
                # Build match reason
                match_reason = ' and '.join(match_reasons) if match_reasons else 'You both have similar aesthetic preferences'
                
                # Get user's recent shares for profile
                recent_shares = db.query(Share).filter_by(
                    user_id=user.user_id
                ).order_by(Share.created_at.desc()).limit(10).all()
                
                # Calculate top categories for matched user
                category_counts_for_match = db.query(
                    Share.category,
                    func.count(Share.id).label('count')
                ).filter_by(user_id=user.user_id).group_by(Share.category).all()
                
                total_shares_for_match = sum([cast(int, c.count) for c in category_counts_for_match], 0)
                top_categories_match = []
                
                if total_shares_for_match > 0:
                    for cat in category_counts_for_match:
                        percentage = round((cast(int, cat.count) / total_shares_for_match) * 100, 1)
                        top_categories_match.append({
                            'category': cat.category,
                            'percentage': percentage
                        })
                    top_categories_match.sort(key=lambda x: x['percentage'], reverse=True)
                
                matches.append({
                    'user': {
                        'userId': user.user_id,
                        'username': user.username,
                        'avatar': user.avatar,
                        'bio': user.bio,
                        'recentShares': [share.to_dict() for share in recent_shares],
                        'auraColors': user.aura_colors or [],
                        'aestheticTags': user.aesthetic_tags or [],
                        'topCategories': top_categories_match
                    },
                    'similarityScore': similarity_score,
                    'sharedAesthetics': list(set(shared_aesthetics)),
                    'matchReason': match_reason
                })
        
        # Sort by similarity score descending
        matches.sort(key=lambda x: x['similarityScore'], reverse=True)
        
        # Paginate
        total = len(matches)
        paginated_matches = matches[offset:offset + limit]
        
        return jsonify({
            'data': paginated_matches,
            'total': total
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@aura_bp.route('/compatibility/<string:user_id>', methods=['GET'])
@jwt_required()
def calculate_compatibility(user_id):
    """
    Calculate compatibility with another user
    ---
    tags:
      - Aura
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: Target user ID to calculate compatibility with
    responses:
      200:
        description: Compatibility score calculated
        schema:
          type: object
          properties:
            compatibilityScore:
              type: integer
              minimum: 0
              maximum: 100
            sharedAesthetics:
              type: array
              items:
                type: string
            matchReason:
              type: string
      401:
        description: Unauthorized
      404:
        description: Target user not found
    """
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        # Cannot calculate compatibility with self
        if current_user_id == user_id:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Cannot calculate compatibility with yourself'
            }), 400
        
        # Get current user
        current_user = db.query(User).filter_by(user_id=current_user_id).first()
        if not current_user:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Current user not found'
            }), 401
        
        # Get target user
        target_user = db.query(User).filter_by(user_id=user_id).first()
        if not target_user:
            return jsonify({
                'error': 'Not Found',
                'message': 'Target user not found'
            }), 404
        
        # Get current user's data
        current_shares = db.query(Share).filter_by(user_id=current_user_id).all()
        current_category_counts = {}
        for share in current_shares:
            current_category_counts[share.category] = current_category_counts.get(share.category, 0) + 1
        
        current_total_shares = len(current_shares)
        # Get aesthetic tags and colors (JSON columns return list or None)
        cur_tags = cast(Optional[List[str]], current_user.aesthetic_tags)
        cur_colors = cast(Optional[List[str]], current_user.aura_colors)
        current_aesthetic_tags = set(cur_tags if cur_tags is not None else [])
        current_aura_colors = set(cur_colors if cur_colors is not None else [])
        
        # Get target user's data
        target_shares = db.query(Share).filter_by(user_id=user_id).all()
        target_category_counts = {}
        for share in target_shares:
            target_category_counts[share.category] = target_category_counts.get(share.category, 0) + 1
        
        target_total_shares = len(target_shares)
        # Get target user aesthetic tags and colors (JSON columns return list or None)
        tgt_tags = cast(Optional[List[str]], target_user.aesthetic_tags)
        tgt_colors = cast(Optional[List[str]], target_user.aura_colors)
        target_aesthetic_tags = set(tgt_tags if tgt_tags is not None else [])
        target_aura_colors = set(tgt_colors if tgt_colors is not None else [])
        
        # Calculate compatibility score
        compatibility_score = 0
        shared_aesthetics = []
        match_reasons = []
        
        # 1. Aesthetic tags comparison (40% weight)
        if current_aesthetic_tags and target_aesthetic_tags:
            shared_tags = current_aesthetic_tags.intersection(target_aesthetic_tags)
            if shared_tags:
                tag_similarity = (len(shared_tags) / len(current_aesthetic_tags.union(target_aesthetic_tags))) * 100
                compatibility_score += tag_similarity * 0.4
                shared_aesthetics.extend(list(shared_tags))
                tags_str = ', '.join(list(shared_tags))
                match_reasons.append(f"You both vibe with {tags_str}")
        
        # 2. Aura colors comparison (20% weight)
        if current_aura_colors and target_aura_colors:
            shared_colors = current_aura_colors.intersection(target_aura_colors)
            if shared_colors:
                color_similarity = (len(shared_colors) / len(current_aura_colors.union(target_aura_colors))) * 100
                compatibility_score += color_similarity * 0.2
                color_count = len(shared_colors)
                plural = 'color' if color_count == 1 else 'colors'
                match_reasons.append(f"You both share {color_count} aura {plural}")
        
        # 3. Category preferences comparison (40% weight)
        if current_total_shares > 0 and target_total_shares > 0:
            all_categories = set(current_category_counts.keys()).union(set(target_category_counts.keys()))
            category_similarity = 0
            shared_categories = []
            
            for category in all_categories:
                current_pct = (current_category_counts.get(category, 0) / current_total_shares) * 100
                target_pct = (target_category_counts.get(category, 0) / target_total_shares) * 100
                
                # Calculate similarity for this category
                category_diff = abs(current_pct - target_pct)
                category_sim = max(0, 100 - category_diff)
                category_similarity += category_sim
                
                # Track shared interests
                if current_pct > 0 and target_pct > 0:
                    shared_categories.append(category)
            
            if len(all_categories) > 0:
                category_similarity = category_similarity / len(all_categories)
                compatibility_score += category_similarity * 0.4
                
                if shared_categories:
                    shared_aesthetics.extend(shared_categories)
                    cats_str = ', '.join(shared_categories)
                    match_reasons.append(f"You both love {cats_str}")
        
        # Round and cap compatibility score
        compatibility_score = min(100, max(0, round(compatibility_score)))
        
        # Build match reason
        if not match_reasons:
            match_reason = "You both have limited shared preferences - explore more content to discover common ground"
        else:
            match_reason = ". ".join(match_reasons)
        
        return jsonify({
            'compatibilityScore': compatibility_score,
            'sharedAesthetics': list(set(shared_aesthetics)),
            'matchReason': match_reason
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
