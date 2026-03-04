"""
Discovery feed endpoint — GET /api/v1/discovery/feed
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc
from app.database import get_db
from app.models.post import Post
from app.models.share import Share
from app.models.user import User

discovery_bp = Blueprint('discovery', __name__)


@discovery_bp.route('/feed', methods=['GET'])
@jwt_required()
def get_discovery_feed():
    """
    Get discovery feed — personalized mix of posts and shares
    ---
    tags:
      - Social
    security:
      - Bearer: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
    responses:
      200:
        description: Discovery feed
        schema:
          type: object
          properties:
            data:
              type: array
              description: Array of mixed content (posts and shares)
            total:
              type: integer
      401:
        description: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)

        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100

        db = get_db()

        # Fetch recent posts (exclude own posts)
        posts = (
            db.query(Post)
            .filter(Post.user_id != current_user_id)
            .order_by(desc(Post.created_at))
            .limit(limit)
            .all()
        )

        # Fetch recent shares (exclude own shares)
        shares = (
            db.query(Share)
            .filter(Share.user_id != current_user_id)
            .order_by(desc(Share.created_at))
            .limit(limit)
            .all()
        )

        # Merge and sort by created_at descending
        feed_items = []

        for post in posts:
            item = post.to_dict()
            item['type'] = 'post'
            feed_items.append((post.created_at, item))

        for share in shares:
            item = share.to_dict()
            item['type'] = 'share'
            # Enrich share with user info
            user = db.query(User).filter_by(user_id=share.user_id).first()
            if user:
                item['username'] = user.username
                item['userAvatar'] = user.avatar
                item['socialMediaLinks'] = user.social_media_links or []
            feed_items.append((share.created_at, item))

        # Sort by timestamp descending and limit
        feed_items.sort(key=lambda x: x[0], reverse=True)
        result = [item for _, item in feed_items[:limit]]

        return jsonify({
            'data': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
