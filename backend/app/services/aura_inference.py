"""
Aura inference service.

Computes a user's aura_colors and aesthetic_tags automatically from their
recent shares and posts.  Called after every share or post creation so the
aura profile stays up-to-date without any manual input from the user.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Optional

# ──────────────────────────────────────────────
# Category → aesthetic tag mapping
# ──────────────────────────────────────────────

CATEGORY_TO_TAGS: dict[str, list[str]] = {
    "cinema": ["film noir", "arthouse", "cinephile", "visual storytelling"],
    "music": ["audiophile", "sonic explorer", "melodic", "vinyl culture"],
    "games": ["gamer", "pixel art", "dystopian", "interactive worlds"],
    "books": ["bibliophile", "literary", "narrative depth", "wordsmith"],
    "travel": ["wanderlust", "nomadic", "cultural explorer", "adventurous"],
}

# Maximum list sizes stored on the user
MAX_AURA_COLORS = 5
MAX_AESTHETIC_TAGS = 10

# Only look at shares/posts from the last 90 days
RECENCY_WINDOW_DAYS = 90

# Hex color validation
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _hex_distance(a: str, b: str) -> float:
    """Euclidean distance in RGB space between two #RRGGBB strings."""
    ra, ga, ba = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    rb, gb, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    return ((ra - rb) ** 2 + (ga - gb) ** 2 + (ba - bb) ** 2) ** 0.5


def _deduplicate_colors(colors: list[str], min_distance: float = 30.0) -> list[str]:
    """
    Remove perceptually-similar colors.
    Keeps the first occurrence when two colors are within *min_distance* in RGB
    space (max possible distance ≈ 441).
    """
    unique: list[str] = []
    for color in colors:
        if not _HEX_RE.match(color):
            continue
        if all(_hex_distance(color, u) >= min_distance for u in unique):
            unique.append(color)
    return unique


# ──────────────────────────────────────────────
# Main inference function
# ──────────────────────────────────────────────

def infer_aura_for_user(db, user_id: str) -> None:
    """
    Recompute and persist ``aura_colors`` and ``aesthetic_tags`` for *user_id*.

    Steps
    -----
    1. Collect recent shares (and posts) within ``RECENCY_WINDOW_DAYS``.
    2. Rank ``dominant_color`` values by recency-weighted frequency.
    3. De-duplicate similar hex values and keep the top ``MAX_AURA_COLORS``.
    4. Derive ``aesthetic_tags`` from the category distribution.
    5. Persist to ``User.aura_colors`` / ``User.aesthetic_tags``.

    This function is intentionally lenient: any individual failure is logged
    but never propagates so that the calling endpoint still succeeds.
    """
    try:
        from app.models.user import User
        from app.models.share import Share
        from app.models.post import Post

        user: Optional[User] = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return

        cutoff = datetime.utcnow() - timedelta(days=RECENCY_WINDOW_DAYS)

        # ── 1. Gather recent shares ───────────────────────────────────────
        shares = (
            db.query(Share)
            .filter(Share.user_id == user_id, Share.created_at >= cutoff)
            .order_by(Share.created_at.desc())
            .limit(50)
            .all()
        )

        # ── 2. Gather recent posts ────────────────────────────────────────
        posts = (
            db.query(Post)
            .filter(Post.user_id == user_id, Post.created_at >= cutoff)
            .order_by(Post.created_at.desc())
            .limit(50)
            .all()
        )

        # ── 3. Build recency-weighted color list ──────────────────────────
        # Assign a weight of 1.0 to the most recent item, linearly decreasing
        # to 0.5 for the oldest item in the window.
        all_items = sorted(
            [
                (s.dominant_color, s.created_at, s.category)
                for s in shares
                if s.dominant_color
            ]
            + [
                (p.dominant_color, p.created_at, p.category)
                for p in posts
                if p.dominant_color
            ],
            key=lambda x: x[1],
            reverse=True,  # newest first
        )

        color_scores: dict[str, float] = {}
        total = len(all_items)

        for rank, (color, _, _) in enumerate(all_items):
            if not color or not _HEX_RE.match(color):
                continue
            weight = 1.0 - (rank / max(total, 1)) * 0.5  # range [0.5 … 1.0]
            color_scores[color.upper()] = (
                color_scores.get(color.upper(), 0.0) + weight
            )

        # Sort by score descending
        ranked_colors = [
            c for c, _ in sorted(color_scores.items(), key=lambda x: -x[1])
        ]

        # De-duplicate perceptually-similar colors
        deduped = _deduplicate_colors(ranked_colors)
        new_aura_colors = deduped[:MAX_AURA_COLORS]

        # ── 4. Derive aesthetic tags from category distribution ───────────
        # Also count categories from items that had *no* dominant_color so that
        # tags reflect the full activity, not just coloured items.
        category_counter: Counter = Counter()
        for share in shares:
            if share.category:
                category_counter[share.category] += 1
        for post in posts:
            if post.category:
                category_counter[post.category] += 1

        # Pick tags for the top categories (up to 3 categories contribute)
        new_tags: list[str] = []
        for cat, _ in category_counter.most_common(3):
            for tag in CATEGORY_TO_TAGS.get(cat, []):
                if tag not in new_tags:
                    new_tags.append(tag)
                if len(new_tags) >= MAX_AESTHETIC_TAGS:
                    break
            if len(new_tags) >= MAX_AESTHETIC_TAGS:
                break

        # ── 5. Persist ────────────────────────────────────────────────────
        # Only overwrite if we actually computed something so that a user with
        # zero shares / no colors keeps whatever was previously set.
        if new_aura_colors:
            user.aura_colors = new_aura_colors
        if new_tags:
            user.aesthetic_tags = new_tags

        db.commit()

    except Exception as exc:
        print(f"[aura_inference] Failed for user {user_id}: {exc}")
        try:
            db.rollback()
        except Exception:
            pass
