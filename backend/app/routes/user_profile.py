from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from urllib.parse import urlparse
from app.database import get_db
from app.models.user import User

user_profile_bp = Blueprint('user_profile', __name__)

# Valid social media platforms per OpenAPI contract
VALID_PLATFORMS = {
    'instagram', 'twitter', 'tiktok', 'youtube', 'facebook',
    'linkedin', 'pinterest', 'spotify', 'twitch', 'other'
}


def _is_valid_url(url: str) -> bool:
    """Validate that url has an http(s) scheme and a non-empty netloc."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False


def validate_social_media_links(links):
    """Validate social media links array. Returns (is_valid, error_message)."""
    if not isinstance(links, list):
        return False, 'socialMediaLinks must be an array'
    
    for i, link in enumerate(links):
        if not isinstance(link, dict):
            return False, f'socialMediaLinks[{i}] must be an object'
        
        platform = link.get('platform')
        url = link.get('url')
        
        if not platform or not url:
            return False, f'socialMediaLinks[{i}] must have both platform and url'
        
        if platform not in VALID_PLATFORMS:
            return False, f'Invalid platform "{platform}". Must be one of: {", ".join(sorted(VALID_PLATFORMS))}'
        
        if not _is_valid_url(url):
            return False, f'Invalid URL for {platform}: "{url}"'
    
    return True, None


@user_profile_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """
    Get current user profile
    ---
    tags:
      - User Profile
    security:
      - Bearer: []
    responses:
      200:
        description: User profile retrieved
      401:
        description: Unauthorized - authentication required
    """
    try:
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()
        
        # Get database session
        db = get_db()
        
        # Find user by ID
        user = db.query(User).filter_by(user_id=current_user_id).first()
        
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404
        
        return jsonify(user.to_dict()), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@user_profile_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """
    Update user profile
    ---
    tags:
      - User Profile
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        description: Profile fields to update
        required: true
        schema:
          type: object
          properties:
            bio:
              type: string
              maxLength: 500
            avatar:
              type: string
              format: uri
            socialMediaLinks:
              type: array
              items:
                type: object
                properties:
                  platform:
                    type: string
                    enum: [instagram, twitter, tiktok, youtube, facebook, linkedin, pinterest, spotify, twitch, other]
                  url:
                    type: string
                    format: uri
    responses:
      200:
        description: Profile updated successfully
      400:
        description: Bad request - validation error
      401:
        description: Unauthorized - authentication required
    """
    db = None
    try:
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        # Get database session
        db = get_db()
        
        # Find user by ID
        user = db.query(User).filter_by(user_id=current_user_id).first()
        
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404
        
        # Update allowed fields
        if 'bio' in data:
            bio = data['bio']
            if bio is not None and len(bio) > 500:
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'Bio must be 500 characters or less'
                }), 400
            user.bio = bio
        
        if 'avatar' in data:
            user.avatar = data['avatar']
        
        # Handle socialMediaLinks
        if 'socialMediaLinks' in data:
            links = data['socialMediaLinks']
            is_valid, error_msg = validate_social_media_links(links)
            if not is_valid:
                return jsonify({
                    'error': 'Bad Request',
                    'message': error_msg
                }), 400
            user.social_media_links = links
        
        # Commit changes
        db.commit()
        db.refresh(user)
        
        return jsonify(user.to_dict()), 200
    
    except Exception as e:
        if db is not None:
            db.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@user_profile_bp.route('/<string:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """
    Get user profile by ID (public endpoint)
    ---
    tags:
      - User Profile
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: User ID
    responses:
      200:
        description: User profile retrieved
      404:
        description: User not found
    """
    try:
        # Get database session
        db = get_db()
        
        # Find user by ID
        user = db.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404
        
        return jsonify(user.to_dict()), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
