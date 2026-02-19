from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from sqlalchemy import desc
from app.database import get_db
from app.models.user import User
from app.models.post import Post, Comment, PostLike

social_bp = Blueprint('social', __name__)


# ──────────────────────────────────────────────
# POST ENDPOINTS
# ──────────────────────────────────────────────

@social_bp.route('/posts', methods=['GET'])
def get_community_posts():
    """
    Get community posts
    ---
    tags:
      - Social
    parameters:
      - name: category
        in: query
        type: string
        description: Filter by category (cinema, music, games, books, travel)
      - name: sortBy
        in: query
        type: string
        description: Sort by (recent, popular)
      - name: limit
        in: query
        type: integer
        default: 20
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: Community posts list
      400:
        description: Bad request
    """
    try:
        db = get_db()
        
        # Get query parameters
        category = request.args.get('category')
        sort_by = request.args.get('sortBy', 'recent')
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = db.query(Post)
        
        # Filter by category if provided
        if category:
            valid_categories = ['cinema', 'music', 'games', 'books', 'travel']
            if category not in valid_categories:
                return jsonify({
                    'error': 'Bad Request',
                    'message': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
                }), 400
            query = query.filter_by(category=category)
        
        # Sort
        if sort_by == 'popular':
            query = query.order_by(desc(Post.likes), desc(Post.created_at))
        else:  # 'recent' or default
            query = query.order_by(desc(Post.created_at))
        
        # Paginate
        posts = query.limit(limit).offset(offset).all()
        
        return jsonify({
            'posts': [post.to_dict() for post in posts],
            'limit': limit,
            'offset': offset,
            'total': query.count()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': 'Invalid limit or offset value'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@social_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_community_post():
    """
    Create a community post
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - category
            - title
            - image
          properties:
            category:
              type: string
              enum: [cinema, music, games, books, travel]
            title:
              type: string
            image:
              type: string
            dominantColor:
              type: string
    responses:
      201:
        description: Post created
      400:
        description: Bad request
      401:
        description: Unauthorized
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        required_fields = ['category', 'title', 'image']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'error': 'Bad Request',
                    'message': f'Field "{field}" is required'
                }), 400
        
        # Validate category
        valid_categories = ['cinema', 'music', 'games', 'books', 'travel']
        if data['category'] not in valid_categories:
            return jsonify({
                'error': 'Bad Request',
                'message': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
            }), 400
        
        # Validate title length
        if len(data['title']) > 255:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Title must be 255 characters or less'
            }), 400
        
        # Create post
        post = Post(
            user_id=current_user_id,
            category=data['category'],
            title=data['title'],
            image=data['image'],
            dominant_color=data.get('dominantColor')
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except:
                pass
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@social_bp.route('/posts/<post_id>', methods=['GET'])
def get_post_by_id(post_id):
    """
    Get post details by ID
    ---
    tags:
      - Social
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Post details
      404:
        description: Post not found
    """
    try:
        db = get_db()
        
        post = db.query(Post).filter_by(id=post_id).first()
        
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post not found'
            }), 404
        
        return jsonify(post.to_dict()), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@social_bp.route('/posts/<post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """
    Delete a post
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
    responses:
      204:
        description: Post deleted
      401:
        description: Unauthorized
      403:
        description: Forbidden - not post owner
      404:
        description: Post not found
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        post = db.query(Post).filter_by(id=post_id).first()
        
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post not found'
            }), 404
        
        # Check if current user is the post owner
        if post.user_id != current_user_id:
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to delete this post'
            }), 403
        
        db.delete(post)
        db.commit()
        
        return '', 204
        
    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except:
                pass
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


# ──────────────────────────────────────────────
# POST LIKE ENDPOINTS
# ──────────────────────────────────────────────

@social_bp.route('/posts/<post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    """
    Like a post
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Post liked
      401:
        description: Unauthorized
      404:
        description: Post not found
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        post = db.query(Post).filter_by(id=post_id).first()
        
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post not found'
            }), 404
        
        # Check if user already liked this post
        existing_like = db.query(PostLike).filter_by(
            post_id=post_id,
            user_id=current_user_id
        ).first()
        
        if existing_like:
            return jsonify({
                'message': 'Post already liked',
                'likes': post.likes
            }), 200
        
        # Create like
        like = PostLike(
            post_id=post_id,
            user_id=current_user_id
        )
        db.add(like)
        
        # Increment like count
        post.likes += 1  # type: ignore
        
        db.commit()
        db.refresh(post)
        
        return jsonify({
            'message': 'Post liked successfully',
            'likes': post.likes
        }), 200
        
    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except:
                pass
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@social_bp.route('/posts/<post_id>/like', methods=['DELETE'])
@jwt_required()
def unlike_post(post_id):
    """
    Unlike a post
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Post unliked
      401:
        description: Unauthorized
      404:
        description: Post not found
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        post = db.query(Post).filter_by(id=post_id).first()
        
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post not found'
            }), 404
        
        # Check if user liked this post
        existing_like = db.query(PostLike).filter_by(
            post_id=post_id,
            user_id=current_user_id
        ).first()
        
        if not existing_like:
            return jsonify({
                'message': 'Post not liked',
                'likes': post.likes
            }), 200
        
        # Remove like
        db.delete(existing_like)
        
        # Decrement like count
        post.likes = max(0, post.likes - 1)  # type: ignore
        
        db.commit()
        db.refresh(post)
        
        return jsonify({
            'message': 'Post unliked successfully',
            'likes': post.likes
        }), 200
        
    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except:
                pass
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


# ──────────────────────────────────────────────
# COMMENT ENDPOINTS
# ──────────────────────────────────────────────

@social_bp.route('/posts/<post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """
    Get post comments
    ---
    tags:
      - Social
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
      - name: limit
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: Post comments
      400:
        description: Bad request
      404:
        description: Post not found
    """
    try:
        db = get_db()
        
        # Check if post exists
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post not found'
            }), 404
        
        # Get limit parameter
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Get comments
        comments = db.query(Comment).filter_by(
            post_id=post_id
        ).order_by(desc(Comment.created_at)).limit(limit).all()
        
        return jsonify({
            'comments': [comment.to_dict() for comment in comments],
            'total': len(comments)
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': 'Invalid limit value'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@social_bp.route('/posts/<post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    """
    Add a comment to a post
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
    responses:
      201:
        description: Comment added
      400:
        description: Bad request
      401:
        description: Unauthorized
      404:
        description: Post not found
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        
        # Check if post exists
        post = db.query(Post).filter_by(id=post_id).first()
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post not found'
            }), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'text' not in data or not data['text']:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Field "text" is required'
            }), 400
        
        # Create comment
        comment = Comment(
            post_id=post_id,
            user_id=current_user_id,
            text=data['text']
        )
        
        db.add(comment)
        
        # Increment comment count
        post.comment_count += 1  # type: ignore
        
        db.commit()
        db.refresh(comment)
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except:
                pass
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
