"""
Badges & Gamification routes

Blueprints:
  badges_bp  → /api/v1/badges
  curator_bp → /api/v1/curator
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy import func
from typing import cast

from app.database import get_db
from app.models.user import User
from app.models.share import Share

### Unnecessary import - badge models are in gamification.py but we want to avoid circular imports
# from app.models.badge import Badge, UserBadge, CuratorLevel, seed_badges_and_levels
from app.models.gamification import Badge, UserBadge, CuratorLevel, seed_badges_and_levels

badges_bp = Blueprint('badges', __name__)
curator_bp = Blueprint('curator', __name__)


# ──────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────

XP_PER_SHARE = 10  # base XP awarded for each share


def _compute_streak(share_dates: list[datetime]) -> int:
    """Return current consecutive-day streak from a list of share datetimes."""
    if not share_dates:
        return 0
    # Deduplicate to dates only
    days = sorted({d.date() for d in share_dates}, reverse=True)
    today = datetime.utcnow().date()
    # Start counting only if the user shared today or yesterday
    if days[0] < today - timedelta(days=1):
        return 0
    streak = 1
    for i in range(1, len(days)):
        if days[i - 1] - days[i] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def _current_level(total_xp: int, levels: list) -> dict:
    """Return the highest level the user has reached."""
    current = levels[0]
    for lvl in levels:
        if total_xp >= lvl.xp_required:
            current = lvl
        else:
            break
    return current


def _evaluate_badges(db, user_id: str, shares) -> dict[str, dict]:
    """
    Compute per-badge progress for a user and upsert UserBadge rows.
    Returns a dict keyed by badge.id → {unlocked, progress, unlocked_at}.
    """
    # Category counts
    category_counts: dict[str, int] = {}
    for s in shares:
        category_counts[s.category] = category_counts.get(s.category, 0) + 1

    total = len(shares)
    streak = _compute_streak([s.created_at for s in shares])
    categories_used = len(category_counts)

    # Define thresholds per badge name
    progress_map: dict[str, int] = {
        'First Share':     min(total, 1),
        'Early Adopter':   1,          # always unlocked if seeded during beta
        'Film Buff':       min(category_counts.get('cinema', 0), 10),
        'Audiophile':      min(category_counts.get('music', 0), 10),
        'Bookworm':        min(category_counts.get('books', 0), 10),
        'Gamer':           min(category_counts.get('games', 0), 10),
        'Wanderer':        min(category_counts.get('travel', 0), 10),
        'All-Rounder':     min(categories_used, 5),
        'Social Butterfly': 0,          # unlock handled externally (aura matches)
        'Trendsetter':     0,           # unlock handled externally (likes)
        '7-Day Streak':    min(streak, 7),
        '30-Day Streak':   min(streak, 30),
        'Tastemaker':      0,           # unlock handled by curator level check below
        'Legend':          0,
    }

    # Fetch all badges & existing user_badges in one go
    all_badges = db.query(Badge).all()
    existing_ubs: dict[str, UserBadge] = {
        ub.badge_id: ub
        for ub in db.query(UserBadge).filter_by(user_id=user_id).all()
    }

    result: dict[str, dict] = {}
    for badge in all_badges:
        progress = progress_map.get(badge.name, 0)
        unlocked = progress >= badge.max_progress

        ub = existing_ubs.get(badge.id)
        if ub is None:
            ub = UserBadge(user_id=user_id, badge_id=badge.id)
            db.add(ub)

        # Only set unlocked_at once
        if unlocked and not ub.unlocked:
            ub.unlocked_at = datetime.utcnow()
        ub.progress = progress
        ub.unlocked = unlocked

        result[badge.id] = {
            'unlocked': ub.unlocked,
            'progress': ub.progress,
            'unlocked_at': ub.unlocked_at,
        }

    db.commit()
    return result


def _build_curator_stats(db, user: User) -> dict:
    """Compute and return curator stats for the given user."""
    shares = db.query(Share).filter_by(user_id=user.user_id).all()
    total_shares = len(shares)
    total_xp = total_shares * XP_PER_SHARE

    levels = db.query(CuratorLevel).order_by(CuratorLevel.level).all()
    if not levels:
        seed_badges_and_levels(db)
        levels = db.query(CuratorLevel).order_by(CuratorLevel.level).all()

    current_level_obj = _current_level(total_xp, levels)

    # XP to next level
    next_levels = [l for l in levels if l.xp_required > total_xp]
    xp_to_next = (next_levels[0].xp_required - total_xp) if next_levels else 0

    streak = _compute_streak([s.created_at for s in shares])

    # Category breakdown
    category_counts: dict[str, int] = {}
    for s in shares:
        category_counts[s.category] = category_counts.get(s.category, 0) + 1

    # Badges
    badge_state = _evaluate_badges(db, user.user_id, shares)
    all_badges = db.query(Badge).all()
    earned_badges = [
        badge.to_dict(
            unlocked=badge_state[badge.id]['unlocked'],
            unlocked_date=badge_state[badge.id]['unlocked_at'],
            progress=badge_state[badge.id]['progress'],
        )
        for badge in all_badges
        if badge.id in badge_state and badge_state[badge.id]['unlocked']
    ]

    # Tastemaker / Legend level check
    if current_level_obj.level >= 10:
        for badge in all_badges:
            if badge.name == 'Legend' and badge.id in badge_state:
                ub = db.query(UserBadge).filter_by(user_id=user.user_id, badge_id=badge.id).first()
                if ub and not ub.unlocked:
                    ub.unlocked = True
                    ub.unlocked_at = datetime.utcnow()
                    ub.progress = 1
                    db.commit()
    if current_level_obj.level >= 5:
        for badge in all_badges:
            if badge.name == 'Tastemaker' and badge.id in badge_state:
                ub = db.query(UserBadge).filter_by(user_id=user.user_id, badge_id=badge.id).first()
                if ub and not ub.unlocked:
                    ub.unlocked = True
                    ub.unlocked_at = datetime.utcnow()
                    ub.progress = 1
                    db.commit()

    return {
        'userId': user.user_id,
        'username': user.username,
        'totalShares': total_shares,
        'totalXP': total_xp,
        'currentLevel': current_level_obj.level,
        'currentLevelName': current_level_obj.name,
        'xpToNextLevel': xp_to_next,
        'streakDays': streak,
        'categoryBreakdown': category_counts,
        'badges': earned_badges,
        'badgeCount': len(earned_badges),
    }


# ──────────────────────────────────────────────────────────────────
# BADGES endpoints
# ──────────────────────────────────────────────────────────────────

@badges_bp.route('', methods=['GET'])
def get_all_badges():
    """
    Get all available badges
    ---
    tags:
      - Badges & Gamification
    parameters:
      - name: rarity
        in: query
        type: string
        enum: [common, rare, epic, legendary]
        description: Filter by rarity
      - name: category
        in: query
        type: string
        enum: [early, completionist, social, streak, special]
        description: Filter by category
    responses:
      200:
        description: List of all badges
        schema:
          type: object
          properties:
            badges:
              type: array
            total:
              type: integer
      400:
        description: Bad request
    """
    try:
        db = get_db()

        # Seed if empty
        count = db.query(func.count(Badge.id)).scalar()
        if count == 0:
            seed_badges_and_levels(db)

        rarity = request.args.get('rarity')
        category = request.args.get('category')

        valid_rarities = {'common', 'rare', 'epic', 'legendary'}
        valid_categories = {'early', 'completionist', 'social', 'streak', 'special'}

        if rarity and rarity not in valid_rarities:
            return jsonify({
                'error': 'Bad Request',
                'message': f'Invalid rarity. Must be one of: {", ".join(valid_rarities)}'
            }), 400

        if category and category not in valid_categories:
            return jsonify({
                'error': 'Bad Request',
                'message': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
            }), 400

        query = db.query(Badge)
        if rarity:
            query = query.filter_by(rarity=rarity)
        if category:
            query = query.filter_by(category=category)

        badges = query.all()

        # If the caller is authenticated, enrich with their unlock state
        user_badge_map: dict[str, UserBadge] = {}
        try:
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
            if current_user_id:
                ubs = db.query(UserBadge).filter_by(user_id=current_user_id).all()
                user_badge_map = {ub.badge_id: ub for ub in ubs}
        except Exception:
            pass

        result = []
        for badge in badges:
            ub = user_badge_map.get(badge.id)
            result.append(badge.to_dict(
                unlocked=ub.unlocked if ub else False,
                unlocked_date=ub.unlocked_at if ub else None,
                progress=ub.progress if ub else 0,
            ))

        return jsonify({
            'badges': result,
            'total': len(result),
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@badges_bp.route('/user', methods=['GET'])
@jwt_required()
def get_current_user_badges():
    """
    Get current user's badges with unlock status and progress
    ---
    tags:
      - Badges & Gamification
    security:
      - Bearer: []
    responses:
      200:
        description: User's badge collection
        schema:
          type: object
          properties:
            badges:
              type: array
            earnedCount:
              type: integer
            totalCount:
              type: integer
      401:
        description: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        db = get_db()

        user = db.query(User).filter_by(user_id=current_user_id).first()
        if not user:
            return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404

        # Seed if needed
        count = db.query(func.count(Badge.id)).scalar()
        if count == 0:
            seed_badges_and_levels(db)

        shares = db.query(Share).filter_by(user_id=current_user_id).all()
        badge_state = _evaluate_badges(db, current_user_id, shares)

        all_badges = db.query(Badge).all()
        result = [
            badge.to_dict(
                unlocked=badge_state.get(badge.id, {}).get('unlocked', False),
                unlocked_date=badge_state.get(badge.id, {}).get('unlocked_at'),
                progress=badge_state.get(badge.id, {}).get('progress', 0),
            )
            for badge in all_badges
        ]

        earned = sum(1 for b in result if b['unlocked'])
        return jsonify({
            'badges': result,
            'earnedCount': earned,
            'totalCount': len(result),
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@badges_bp.route('/user/<user_id>', methods=['GET'])
def get_user_badges_by_id(user_id: str):
    """
    Get a specific user's badges
    ---
    tags:
      - Badges & Gamification
    parameters:
      - name: user_id
        in: path
        required: true
        type: string
        description: Target user ID
    responses:
      200:
        description: User's badge collection
      404:
        description: User not found
    """
    try:
        db = get_db()

        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404

        count = db.query(func.count(Badge.id)).scalar()
        if count == 0:
            seed_badges_and_levels(db)

        shares = db.query(Share).filter_by(user_id=user_id).all()
        badge_state = _evaluate_badges(db, user_id, shares)

        all_badges = db.query(Badge).all()
        result = [
            badge.to_dict(
                unlocked=badge_state.get(badge.id, {}).get('unlocked', False),
                unlocked_date=badge_state.get(badge.id, {}).get('unlocked_at'),
                progress=badge_state.get(badge.id, {}).get('progress', 0),
            )
            for badge in all_badges
        ]

        earned = sum(1 for b in result if b['unlocked'])
        return jsonify({
            'userId': user_id,
            'username': user.username,
            'badges': result,
            'earnedCount': earned,
            'totalCount': len(result),
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


# ──────────────────────────────────────────────────────────────────
# CURATOR endpoints
# ──────────────────────────────────────────────────────────────────

@curator_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_curator_stats():
    """
    Get current user's curator statistics
    ---
    tags:
      - Badges & Gamification
    security:
      - Bearer: []
    responses:
      200:
        description: Curator statistics
        schema:
          type: object
          properties:
            userId:
              type: string
            totalShares:
              type: integer
            totalXP:
              type: integer
            currentLevel:
              type: integer
            currentLevelName:
              type: string
            xpToNextLevel:
              type: integer
            streakDays:
              type: integer
            categoryBreakdown:
              type: object
            badges:
              type: array
            badgeCount:
              type: integer
      401:
        description: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        db = get_db()

        user = db.query(User).filter_by(user_id=current_user_id).first()
        if not user:
            return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404

        # Ensure levels exist
        lvl_count = db.query(func.count(CuratorLevel.level)).scalar()
        if lvl_count == 0:
            seed_badges_and_levels(db)

        stats = _build_curator_stats(db, user)
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@curator_bp.route('/stats/<user_id>', methods=['GET'])
def get_curator_stats_by_user_id(user_id: str):
    """
    Get a specific user's curator statistics
    ---
    tags:
      - Badges & Gamification
    parameters:
      - name: user_id
        in: path
        required: true
        type: string
        description: Target user ID
    responses:
      200:
        description: Curator statistics
      404:
        description: User not found
    """
    try:
        db = get_db()

        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404

        lvl_count = db.query(func.count(CuratorLevel.level)).scalar()
        if lvl_count == 0:
            seed_badges_and_levels(db)

        stats = _build_curator_stats(db, user)
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@curator_bp.route('/levels', methods=['GET'])
def get_curator_levels():
    """
    Get all curator progression levels
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
            total:
              type: integer
      400:
        description: Bad request
    """
    try:
        db = get_db()

        lvl_count = db.query(func.count(CuratorLevel.level)).scalar()
        if lvl_count == 0:
            seed_badges_and_levels(db)

        levels = db.query(CuratorLevel).order_by(CuratorLevel.level).all()
        return jsonify({
            'levels': [lvl.to_dict() for lvl in levels],
            'total': len(levels),
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
