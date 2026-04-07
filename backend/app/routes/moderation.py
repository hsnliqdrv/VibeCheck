from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import desc

from app.database import get_db
from app.models.post import Post
from app.models.report import RoomPostReport
from app.models.room import AestheticRoom
from app.models.user import User

moderation_bp = Blueprint('moderation', __name__)


def _get_moderator_or_error(db, user_id):
    user = db.query(User).filter_by(user_id=user_id).first()
    if user is None:
        return None, (jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401)
    if user.role != 'moderator':
        return None, (jsonify({'error': 'Forbidden', 'message': 'Moderator access required'}), 403)
    return user, None


@moderation_bp.route('/reports', methods=['GET'])
@jwt_required()
def list_reports():
    db = get_db()
    current_user_id = get_jwt_identity()

    _, error = _get_moderator_or_error(db, current_user_id)
    if error:
        return error

    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({'error': 'Bad Request', 'message': 'Invalid limit or offset'}), 400

    report_rows = db.query(RoomPostReport).order_by(desc(RoomPostReport.created_at)).limit(limit).offset(offset).all()
    total = db.query(RoomPostReport).count()

    items = []
    for report in report_rows:
        report_dict = report.to_dict()
        post = db.query(Post).filter_by(id=report.post_id).first()
        room = db.query(AestheticRoom).filter_by(id=report.room_id).first()
        reporter = db.query(User).filter_by(user_id=report.reporter_id).first()
        owner = db.query(User).filter_by(user_id=report.post_owner_id).first()

        items.append({
            'report': report_dict,
            'room': {
                'id': room.id,
                'name': room.name,
            } if room is not None else None,
            'post': {
                'id': post.id,
                'title': post.title,
                'image': post.image,
                'category': post.category,
                'createdAt': post.created_at.isoformat(),
            } if post is not None else None,
            'reporter': {
                'userId': reporter.user_id,
                'username': reporter.username,
                'email': reporter.email,
            } if reporter is not None else None,
            'owner': {
                'userId': owner.user_id,
                'username': owner.username,
                'email': owner.email,
                'suspendedUntil': owner.to_dict().get('suspendedUntil'),
                'suspensionReason': owner.to_dict().get('suspensionReason'),
            } if owner is not None else None,
        })

    return jsonify({
        'data': items,
        'total': total,
        'limit': limit,
        'offset': offset,
    }), 200


@moderation_bp.route('/users/<string:user_id>/suspend', methods=['POST'])
@jwt_required()
def suspend_user(user_id):
    db = get_db()
    current_user_id = get_jwt_identity()

    _, error = _get_moderator_or_error(db, current_user_id)
    if error:
        return error

    data = request.get_json() or {}
    duration_hours = data.get('durationHours')
    reason = (data.get('reason') or '').strip() or None

    if duration_hours is None:
        return jsonify({'error': 'Bad Request', 'message': 'Field "durationHours" is required'}), 400

    try:
        duration_hours = int(duration_hours)
    except (TypeError, ValueError):
        return jsonify({'error': 'Bad Request', 'message': 'durationHours must be an integer'}), 400

    if duration_hours <= 0 or duration_hours > 24 * 365:
        return jsonify({'error': 'Bad Request', 'message': 'durationHours must be between 1 and 8760'}), 400

    user = db.query(User).filter_by(user_id=user_id).first()
    if user is None:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404

    if bool(user.role == 'moderator'):
        return jsonify({'error': 'Forbidden', 'message': 'Moderators cannot be suspended'}), 403

    setattr(user, 'suspended_until', datetime.utcnow() + timedelta(hours=duration_hours))
    setattr(user, 'suspension_reason', reason)
    db.commit()
    db.refresh(user)

    return jsonify({
        'message': 'User suspended successfully',
        'user': user.to_dict(),
    }), 200


@moderation_bp.route('/room-posts/<string:post_id>', methods=['DELETE'])
@jwt_required()
def delete_room_post(post_id):
    db = get_db()
    current_user_id = get_jwt_identity()

    _, error = _get_moderator_or_error(db, current_user_id)
    if error:
        return error

    post = db.query(Post).filter_by(id=post_id).first()
    if post is None:
        return jsonify({'error': 'Not Found', 'message': 'Post not found'}), 404
    if post.room_id is None:
        return jsonify({'error': 'Bad Request', 'message': 'Only room posts can be deleted from moderation'}), 400

    room = db.query(AestheticRoom).filter_by(id=post.room_id).first()
    if room is not None:
        room.post_count = max(0, room.post_count - 1)  # type: ignore

    db.query(RoomPostReport).filter_by(post_id=post_id).delete()
    db.delete(post)
    db.commit()

    return '', 204
