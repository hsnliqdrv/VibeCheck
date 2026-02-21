from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_db
from app.models.user import User

user_profile_bp = Blueprint('user_profile', __name__)


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
        schema:
          type: object
          properties:
            userId:
              type: string
              example: u_123abc456def
            email:
              type: string
              example: user@example.com
            username:
              type: string
              example: aesthetic_anna
            avatar:
              type: string
              nullable: true
              example: https://example.com/avatar.jpg
            bio:
              type: string
              nullable: true
              example: "Lover of minimalist aesthetics"
            createdAt:
              type: string
              format: date-time
            updatedAt:
              type: string
              format: date-time
      401:
        description: Unauthorized - authentication required
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
            message:
              type: string
              example: Missing or invalid authentication token
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
              example: "Lover of minimalist aesthetics"
            avatar:
              type: string
              format: uri
              example: https://example.com/avatar.jpg
    responses:
      200:
        description: Profile updated successfully
        schema:
          type: object
          properties:
            userId:
              type: string
              example: u_123abc456def
            email:
              type: string
              example: user@example.com
            username:
              type: string
              example: aesthetic_anna
            avatar:
              type: string
              nullable: true
              example: https://example.com/avatar.jpg
            bio:
              type: string
              nullable: true
              example: "Lover of minimalist aesthetics"
            createdAt:
              type: string
              format: date-time
            updatedAt:
              type: string
              format: date-time
      400:
        description: Bad request - validation error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Bad Request
            message:
              type: string
              example: Bio must be 500 characters or less
      401:
        description: Unauthorized - authentication required
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
            message:
              type: string
              example: Missing or invalid authentication token
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
        example: u_123abc456def
    responses:
      200:
        description: User profile retrieved
        schema:
          type: object
          properties:
            userId:
              type: string
              example: u_123abc456def
            email:
              type: string
              example: user@example.com
            username:
              type: string
              example: aesthetic_anna
            avatar:
              type: string
              nullable: true
              example: https://example.com/avatar.jpg
            bio:
              type: string
              nullable: true
              example: "Lover of minimalist aesthetics"
            createdAt:
              type: string
              format: date-time
            updatedAt:
              type: string
              format: date-time
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: Not Found
            message:
              type: string
              example: User not found
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
