from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.share import Share

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
        
        total_shares = sum(c.count for c in category_counts)
        top_categories = []
        
        if total_shares > 0:
            for cat in category_counts:
                percentage = round((cat.count / total_shares) * 100, 1)
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
        
        # Update aesthetic tags
        if 'aestheticTags' in data:
            if not isinstance(data['aestheticTags'], list):
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'aestheticTags must be an array'
                }), 400
            user.aesthetic_tags = data['aestheticTags']
        
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
        
        total_shares = sum(c.count for c in category_counts)
        top_categories = []
        
        if total_shares > 0:
            for cat in category_counts:
                percentage = round((cat.count / total_shares) * 100, 1)
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
        
        total_shares = sum(c.count for c in category_counts)
        top_categories = []
        
        if total_shares > 0:
            for cat in category_counts:
                percentage = round((cat.count / total_shares) * 100, 1)
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
        
        return jsonify(new_share.to_dict()), 201
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
