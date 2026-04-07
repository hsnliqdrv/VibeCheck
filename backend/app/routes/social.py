from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from sqlalchemy import desc
from app.database import get_db
from app.models.user import User
from app.models.post import Post, Comment, PostLike
from app.models.room import AestheticRoom, RoomMember
from app.models.report import RoomPostReport
from app.services.badge_service import BadgeService

social_bp = Blueprint('social', __name__)


def _get_optional_user_id():
    """Return current user id when JWT is valid and present; otherwise None."""
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()
    except Exception:
        return None


def _get_suspension_error(user):
    if user is not None and bool(user.suspended_until) and user.suspended_until > datetime.utcnow():
        return jsonify({
            'error': 'Forbidden',
            'message': 'Your account is suspended',
            'suspendedUntil': user.suspended_until.isoformat(),
            'reason': user.suspension_reason,
        }), 403
    return None


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

        posts_data = [post.to_dict() for post in posts]

        current_user_id = _get_optional_user_id()
        if current_user_id and posts:
            post_ids = [post.id for post in posts]
            liked_post_rows = db.query(PostLike.post_id).filter(
                PostLike.user_id == current_user_id,
                PostLike.post_id.in_(post_ids),
            ).all()
            liked_post_ids = {post_id for (post_id,) in liked_post_rows}
            for post_data in posts_data:
                post_data['liked'] = post_data['id'] in liked_post_ids
        
        return jsonify({
            'posts': posts_data,
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

        current_user = db.query(User).filter_by(user_id=current_user_id).first()
        suspension_error = _get_suspension_error(current_user)
        if suspension_error:
          return suspension_error
        
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
        
        # Update user curator stats
        try:
            from app.models.gamification import UserCuratorStats
            stats = db.query(UserCuratorStats).filter_by(user_id=current_user_id).first()
            if not stats:
                stats = UserCuratorStats(user_id=current_user_id)
                db.add(stats)
            
            # Increment total posts
            stats.total_posts += 1  # type: ignore
            
            # Award XP for creating a post (5 XP)
            stats.total_xp += 5  # type: ignore
            stats.current_xp += 5  # type: ignore
            
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
            print(f"Stats update error: {stats_error}")
        
        # Check and unlock badges
        try:
            BadgeService.check_and_unlock_badges(current_user_id)
        except Exception as badge_error:
            # Don't fail the request if badge checking fails
            print(f"Badge unlock error: {badge_error}")

        # Recompute aura profile (colors + tags) from latest activity
        try:
            from app.services.aura_inference import infer_aura_for_user
            infer_aura_for_user(db, current_user_id)
        except Exception as aura_error:
            print(f"Aura inference error: {aura_error}")

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
        
        # Store post data before deletion for stats update
        post_likes = post.likes
        post_comments = post.comment_count
        
        db.delete(post)
        db.commit()
        
        # Update user curator stats
        try:
            from app.models.gamification import UserCuratorStats
            stats = db.query(UserCuratorStats).filter_by(user_id=current_user_id).first()
            if stats:
                # Decrement total posts
                stats.total_posts = max(0, stats.total_posts - 1)  # type: ignore
                
                # Decrement likes and comments received
                stats.total_likes_received = max(0, stats.total_likes_received - post_likes)  # type: ignore
                stats.total_comments_received = max(0, stats.total_comments_received - post_comments)  # type: ignore
                
                # Remove XP (5 for post + 2 per like + 3 per comment)
                xp_to_remove = 5 + (post_likes * 2) + (post_comments * 3)
                stats.total_xp = max(0, stats.total_xp - xp_to_remove)  # type: ignore
                stats.current_xp = max(0, stats.current_xp - xp_to_remove)  # type: ignore
                
                db.commit()
        except Exception as stats_error:
            print(f"Stats update error: {stats_error}")
        
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
        
        # Update post owner's stats
        try:
            from app.models.gamification import UserCuratorStats
            stats = db.query(UserCuratorStats).filter_by(user_id=post.user_id).first()
            if not stats:
                stats = UserCuratorStats(user_id=post.user_id)
                db.add(stats)
            
            # Increment likes received
            stats.total_likes_received += 1  # type: ignore
            
            # Award XP to post owner (2 XP per like received)
            stats.total_xp += 2  # type: ignore
            stats.current_xp += 2  # type: ignore
            
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
            print(f"Stats update error: {stats_error}")
        
        # Check and unlock badges for both liker and post owner
        try:
            BadgeService.check_and_unlock_badges(current_user_id)
            if post.user_id != current_user_id:
                BadgeService.check_and_unlock_badges(post.user_id)
        except Exception as badge_error:
            # Don't fail the request if badge checking fails
            print(f"Badge unlock error: {badge_error}")
        
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
        
        # Update post owner's stats
        try:
            from app.models.gamification import UserCuratorStats
            stats = db.query(UserCuratorStats).filter_by(user_id=post.user_id).first()
            if stats:
                # Decrement likes received
                stats.total_likes_received = max(0, stats.total_likes_received - 1)  # type: ignore
                
                # Remove XP (2 XP per like)
                stats.total_xp = max(0, stats.total_xp - 2)  # type: ignore
                stats.current_xp = max(0, stats.current_xp - 2)  # type: ignore
                
                db.commit()
        except Exception as stats_error:
            print(f"Stats update error: {stats_error}")
        
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
        
        # Update post owner's stats
        try:
            from app.models.gamification import UserCuratorStats
            stats = db.query(UserCuratorStats).filter_by(user_id=post.user_id).first()
            if not stats:
                stats = UserCuratorStats(user_id=post.user_id)
                db.add(stats)
            
            # Increment comments received
            stats.total_comments_received += 1  # type: ignore
            
            # Award XP to post owner (3 XP per comment received)
            stats.total_xp += 3  # type: ignore
            stats.current_xp += 3  # type: ignore
            
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
            print(f"Stats update error: {stats_error}")
        
        # Check badges for post owner
        try:
            if post.user_id != current_user_id:
                BadgeService.check_and_unlock_badges(post.user_id)
        except Exception as badge_error:
            print(f"Badge unlock error: {badge_error}")
        
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


# ──────────────────────────────────────────────
# ROOM ENDPOINTS
# ──────────────────────────────────────────────

@social_bp.route('/rooms', methods=['GET'])
def get_rooms():
    """
    Get aesthetic rooms
    ---
    tags:
      - Social
    parameters:
      - name: trending
        in: query
        type: boolean
        description: Filter to only trending rooms
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
        description: Aesthetic rooms list
      400:
        description: Bad request
    """
    try:
        db = get_db()

        trending_param = request.args.get('trending')
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))

        query = db.query(AestheticRoom)
        if trending_param is not None:
            query = query.filter_by(trending=(trending_param.lower() == 'true'))

        total = query.count()
        rooms = query.order_by(desc(AestheticRoom.member_count)).limit(limit).offset(offset).all()

        rooms_data = [room.to_dict() for room in rooms]

        current_user_id = _get_optional_user_id()
        if current_user_id and rooms:
            room_ids = [room.id for room in rooms]
            joined_room_rows = db.query(RoomMember.room_id).filter(
                RoomMember.user_id == current_user_id,
                RoomMember.room_id.in_(room_ids),
            ).all()
            joined_room_ids = {room_id for (room_id,) in joined_room_rows}
            for room_data in rooms_data:
                room_data['joined'] = room_data['id'] in joined_room_ids

        return jsonify({
            'data': rooms_data,
            'total': total,
            'limit': limit,
            'offset': offset,
        }), 200

    except ValueError:
        return jsonify({'error': 'Bad Request', 'message': 'Invalid limit or offset'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@social_bp.route('/rooms/<string:room_id>', methods=['GET'])
def get_room(room_id):
    """
    Get room details
    ---
    tags:
      - Social
    parameters:
      - name: room_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Room details
      404:
        description: Room not found
    """
    try:
        db = get_db()
        room = db.query(AestheticRoom).filter_by(id=room_id).first()
        if not room:
            return jsonify({'error': 'Not Found', 'message': 'Room not found'}), 404

        room_data = room.to_dict()
        current_user_id = _get_optional_user_id()
        if current_user_id:
            joined = db.query(RoomMember).filter_by(
                room_id=room_id,
                user_id=current_user_id,
            ).first() is not None
            room_data['joined'] = joined

        return jsonify(room_data), 200
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@social_bp.route('/rooms/<string:room_id>/posts', methods=['GET'])
def get_room_posts(room_id):
    """
    Get posts in a room
    ---
    tags:
      - Social
    parameters:
      - name: room_id
        in: path
        type: string
        required: true
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
        description: Room posts list
      404:
        description: Room not found
    """
    try:
        db = get_db()

        room = db.query(AestheticRoom).filter_by(id=room_id).first()
        if not room:
            return jsonify({'error': 'Not Found', 'message': 'Room not found'}), 404

        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))

        query = db.query(Post).filter_by(room_id=room_id).order_by(desc(Post.created_at))
        total = query.count()
        posts = query.limit(limit).offset(offset).all()

        posts_data = [post.to_dict() for post in posts]

        current_user_id = _get_optional_user_id()
        if current_user_id and posts:
            post_ids = [post.id for post in posts]
            liked_post_rows = db.query(PostLike.post_id).filter(
                PostLike.user_id == current_user_id,
                PostLike.post_id.in_(post_ids),
            ).all()
            liked_post_ids = {post_id for (post_id,) in liked_post_rows}
            for post_data in posts_data:
                post_data['liked'] = post_data['id'] in liked_post_ids

        return jsonify({
            'data': posts_data,
            'total': total,
            'limit': limit,
            'offset': offset,
        }), 200

    except ValueError:
        return jsonify({'error': 'Bad Request', 'message': 'Invalid limit or offset'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@social_bp.route('/rooms/<string:room_id>/posts', methods=['POST'])
@jwt_required()
def create_room_post(room_id):
    """
    Create a post inside a specific room
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: room_id
        in: path
        type: string
        required: true
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
      404:
        description: Room not found
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()

        current_user = db.query(User).filter_by(user_id=current_user_id).first()
        suspension_error = _get_suspension_error(current_user)
        if suspension_error:
          return suspension_error

        room = db.query(AestheticRoom).filter_by(id=room_id).first()
        if not room:
            return jsonify({'error': 'Not Found', 'message': 'Room not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Bad Request', 'message': 'Request body is required'}), 400

        required_fields = ['category', 'title', 'image']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': 'Bad Request', 'message': f'Field "{field}" is required'}), 400

        valid_categories = ['cinema', 'music', 'games', 'books', 'travel']
        if data['category'] not in valid_categories:
            return jsonify({
                'error': 'Bad Request',
                'message': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
            }), 400

        if len(data['title']) > 255:
            return jsonify({'error': 'Bad Request', 'message': 'Title must be 255 characters or less'}), 400

        post = Post(
            user_id=current_user_id,
            category=data['category'],
            title=data['title'],
            image=data['image'],
            dominant_color=data.get('dominantColor'),
            room_id=room_id,
        )
        db.add(post)

        # Update room post count
        room.post_count += 1  # type: ignore

        db.commit()
        db.refresh(post)

        # Update user curator stats
        try:
            from app.models.gamification import UserCuratorStats, CuratorLevel
            stats = db.query(UserCuratorStats).filter_by(user_id=current_user_id).first()
            if not stats:
                stats = UserCuratorStats(user_id=current_user_id)
                db.add(stats)
            stats.total_posts += 1  # type: ignore
            stats.total_xp += 5  # type: ignore
            stats.current_xp += 5  # type: ignore
            next_level = db.query(CuratorLevel).filter(
                CuratorLevel.level == stats.current_level + 1
            ).first()
            if next_level is not None and stats.total_xp >= next_level.xp_required:  # type: ignore
                stats.current_level = next_level.level  # type: ignore
                stats.current_xp = stats.total_xp - next_level.xp_required  # type: ignore
            db.commit()
        except Exception as stats_error:
            print(f"Stats update error: {stats_error}")

        # Check badges
        try:
            BadgeService.check_and_unlock_badges(current_user_id)
        except Exception as badge_error:
            print(f"Badge unlock error: {badge_error}")

        # Recompute aura profile
        try:
            from app.services.aura_inference import infer_aura_for_user
            infer_aura_for_user(db, current_user_id)
        except Exception as aura_error:
            print(f"Aura inference error: {aura_error}")

        return jsonify({'message': 'Post created successfully', 'post': post.to_dict()}), 201

    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@social_bp.route('/rooms/<string:room_id>/posts/<string:post_id>/report', methods=['POST'])
@jwt_required()
def report_room_post(room_id, post_id):
    """
    Report a post inside a specific room
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: room_id
        in: path
        type: string
        required: true
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
            - reason
          properties:
            reason:
              type: string
              maxLength: 500
    responses:
      201:
        description: Report created
      400:
        description: Bad request
      401:
        description: Unauthorized
      404:
        description: Room or post not found
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()

        current_user = db.query(User).filter_by(user_id=current_user_id).first()
        suspension_error = _get_suspension_error(current_user)
        if suspension_error:
          return suspension_error

        room = db.query(AestheticRoom).filter_by(id=room_id).first()
        if not room:
            return jsonify({'error': 'Not Found', 'message': 'Room not found'}), 404

        post = db.query(Post).filter_by(id=post_id, room_id=room_id).first()
        if not post:
            return jsonify({'error': 'Not Found', 'message': 'Post not found in this room'}), 404

        data = request.get_json() or {}
        reason = (data.get('reason') or '').strip()
        if not reason:
            return jsonify({'error': 'Bad Request', 'message': 'Field "reason" is required'}), 400
        if len(reason) > 500:
            return jsonify({'error': 'Bad Request', 'message': 'Reason must be 500 characters or less'}), 400

        report = RoomPostReport(
            room_id=room_id,
            post_id=post_id,
            reporter_id=current_user_id,
            post_owner_id=post.user_id,
            reason=reason,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return jsonify({
            'message': 'Report submitted successfully',
            'report': report.to_dict(),
        }), 201

    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@social_bp.route('/rooms/<string:room_id>/join', methods=['POST'])
@jwt_required()
def join_room(room_id):
    """
    Join an aesthetic room
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: room_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Joined room
      401:
        description: Unauthorized
      404:
        description: Room not found
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()

        room = db.query(AestheticRoom).filter_by(id=room_id).first()
        if not room:
            return jsonify({'error': 'Not Found', 'message': 'Room not found'}), 404

        # Idempotent – silently succeed if already a member
        existing = db.query(RoomMember).filter_by(
            room_id=room_id, user_id=current_user_id
        ).first()

        if not existing:
            membership = RoomMember(room_id=room_id, user_id=current_user_id)
            db.add(membership)
            room.member_count += 1  # type: ignore

            # Update gamification stats
            try:
                from app.models.gamification import UserCuratorStats
                stats = db.query(UserCuratorStats).filter_by(user_id=current_user_id).first()
                if not stats:
                    stats = UserCuratorStats(user_id=current_user_id)
                    db.add(stats)
                stats.rooms_joined += 1  # type: ignore
            except Exception as stats_error:
                print(f"Stats update error: {stats_error}")

            db.commit()

        return jsonify(room.to_dict()), 200

    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@social_bp.route('/rooms/<string:room_id>/leave', methods=['POST'])
@jwt_required()
def leave_room(room_id):
    """
    Leave an aesthetic room
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: room_id
        in: path
        type: string
        required: true
    responses:
      204:
        description: Left room
      401:
        description: Unauthorized
      404:
        description: Room not found
    """
    db = None
    try:
        current_user_id = get_jwt_identity()
        db = get_db()

        room = db.query(AestheticRoom).filter_by(id=room_id).first()
        if not room:
            return jsonify({'error': 'Not Found', 'message': 'Room not found'}), 404

        membership = db.query(RoomMember).filter_by(
            room_id=room_id, user_id=current_user_id
        ).first()

        if membership:
            db.delete(membership)
            room.member_count = max(0, room.member_count - 1)  # type: ignore

            # Update gamification stats
            try:
                from app.models.gamification import UserCuratorStats
                stats = db.query(UserCuratorStats).filter_by(user_id=current_user_id).first()
                if stats:
                    stats.rooms_joined = max(0, stats.rooms_joined - 1)  # type: ignore
            except Exception as stats_error:
                print(f"Stats update error: {stats_error}")

            db.commit()

        return '', 204

    except Exception as e:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
