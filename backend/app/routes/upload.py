"""
Upload routes for handling file uploads to DigitalOcean Spaces
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.spaces import SpacesService
from flask import current_app
import logging

logger = logging.getLogger(__name__)
upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """
    Get presigned URL for avatar upload
    ---
    tags:
      - Upload
    security:
      - Bearer: []
    parameters:
      - in: query
        name: file_extension
        type: string
        required: true
        description: File extension (jpg, jpeg, png, webp)
        example: jpg
    responses:
      200:
        description: Presigned URL generated successfully
        schema:
          type: object
          properties:
            presigned_url:
              type: string
              description: Presigned URL for uploading the file
              example: "https://fra1.digitaloceanspaces.com/..."
            file_key:
              type: string
              description: The key/path where the file will be stored
              example: "avatars/user123/avatar.png"
            bucket:
              type: string
              description: The bucket name
              example: "vibecheck"
            cdn_url:
              type: string
              description: CDN URL to access the file after upload
              example: "https://cdn.vibeaura.app/avatars/user123/avatar.png"
      400:
        description: Invalid request or file extension
        schema:
          type: object
          properties:
            error:
              type: string
              example: "file_extension parameter is required"
      401:
        description: Unauthorized - missing or invalid token
      500:
        description: Server error
    """
    try:
        # Get file extension from query parameters
        file_extension = request.args.get('file_extension', '').strip()
        
        if not file_extension:
            return jsonify({'error': 'file_extension parameter is required'}), 400
        
        # Validate file extension
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
        if file_extension.lower() not in allowed_extensions:
            return jsonify({
                'error': 'Invalid file extension',
                'allowed': allowed_extensions,
                'max_size_mb': current_app.config['AVATAR_MAX_SIZE'] // (1024 * 1024)
            }), 400
        
        # Get current user ID
        user_id = get_jwt_identity()
        logger.info(f"Avatar upload requested by user: {user_id}, extension: {file_extension}")
        
        # Generate presigned URL
        spaces_service = SpacesService()
        result = spaces_service.generate_avatar_presigned_url(user_id, file_extension)
        
        # Get CDN URL for the file
        cdn_url = spaces_service.get_cdn_url(result['file_key'])
        
        return jsonify({
            'presigned_url': result['presigned_url'],
            'file_key': result['file_key'],
            'bucket': result['bucket'],
            'cdn_url': cdn_url,
            'upload_method': 'PUT',
            'max_size_bytes': current_app.config['AVATAR_MAX_SIZE'],
            'allowed_types': current_app.config['AVATAR_ALLOWED_TYPES'],
            'expires_in_seconds': current_app.config['PRESIGNED_URL_EXPIRY']
        }), 200
    
    except ValueError as e:
        logger.error(f"Validation error in avatar upload: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating presigned URL for avatar: {str(e)}")
        return jsonify({'error': 'Failed to generate presigned URL', 'details': str(e)}), 500


@upload_bp.route('/post', methods=['POST'])
@jwt_required()
def upload_post_image():
    """
    Get presigned URL for post image upload
    ---
    tags:
      - Upload
    security:
      - Bearer: []
    parameters:
      - in: query
        name: file_extension
        type: string
        required: true
        description: File extension (jpg, jpeg, png, webp, gif)
        example: jpg
    responses:
      200:
        description: Presigned URL generated successfully
        schema:
          type: object
          properties:
            presigned_url:
              type: string
              description: Presigned URL for uploading the file
              example: "https://fra1.digitaloceanspaces.com/..."
            file_key:
              type: string
              description: The key/path where the file will be stored
              example: "posts/user123/post-id-xyz/image.jpg"
            bucket:
              type: string
              description: The bucket name
              example: "vibecheck"
            post_id:
              type: string
              description: Generated post ID for reference
              example: "550e8400-e29b-41d4-a716-446655440000"
            cdn_url:
              type: string
              description: CDN URL to access the file after upload
              example: "https://cdn.vibeaura.app/posts/user123/post-id-xyz/image.jpg"
      400:
        description: Invalid request or file extension
        schema:
          type: object
          properties:
            error:
              type: string
              example: "file_extension parameter is required"
      401:
        description: Unauthorized - missing or invalid token
      500:
        description: Server error
    """
    try:
        # Get file extension from query parameters
        file_extension = request.args.get('file_extension', '').strip()
        
        if not file_extension:
            return jsonify({'error': 'file_extension parameter is required'}), 400
        
        # Validate file extension
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp', 'gif']
        if file_extension.lower() not in allowed_extensions:
            return jsonify({
                'error': 'Invalid file extension',
                'allowed': allowed_extensions,
                'max_size_mb': current_app.config['POST_IMAGE_MAX_SIZE'] // (1024 * 1024)
            }), 400
        
        # Get current user ID
        user_id = get_jwt_identity()
        
        # Generate presigned URL
        spaces_service = SpacesService()
        result = spaces_service.generate_post_image_presigned_url(user_id, file_extension)
        
        # Get CDN URL for the file
        cdn_url = spaces_service.get_cdn_url(result['file_key'])
        
        return jsonify({
            'presigned_url': result['presigned_url'],
            'file_key': result['file_key'],
            'bucket': result['bucket'],
            'post_id': result['post_id'],
            'cdn_url': cdn_url,
            'upload_method': 'PUT',
            'max_size_bytes': current_app.config['POST_IMAGE_MAX_SIZE'],
            'allowed_types': current_app.config['POST_IMAGE_ALLOWED_TYPES'],
            'expires_in_seconds': current_app.config['PRESIGNED_URL_EXPIRY']
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to generate presigned URL', 'details': str(e)}), 500
