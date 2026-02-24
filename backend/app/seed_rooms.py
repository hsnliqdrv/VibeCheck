"""
Seed script for VibeCheck aesthetic rooms.
"""
from typing import List, Dict

from app.models.room import AestheticRoom


DEFAULT_ROOMS: List[Dict[str, object]] = [
    {
        "name": "Dark Academia",
        "hashtag": "#darkacademia",
        "description": "Moody libraries, candlelit desks, and old-world charm.",
        "cover_gradient": "linear-gradient(135deg, #1b1b3a, #693668)",
        "member_count": 0,
        "post_count": 0,
        "trending": True,
        "moderators": [],
    },
    {
        "name": "Coastal Indie",
        "hashtag": "#coastalindie",
        "description": "Sea-breeze aesthetics, washed denim, and slow guitars.",
        "cover_gradient": "linear-gradient(135deg, #0f4c5c, #9a8c98)",
        "member_count": 0,
        "post_count": 0,
        "trending": False,
        "moderators": [],
    },
    {
        "name": "Neon Arcade",
        "hashtag": "#neonarcade",
        "description": "Synth glow, pixel nostalgia, and late-night city lights.",
        "cover_gradient": "linear-gradient(135deg, #2b0f54, #ff3c7d)",
        "member_count": 0,
        "post_count": 0,
        "trending": True,
        "moderators": [],
    },
]


def seed_rooms(db) -> int:
    """Seed default aesthetic rooms if none exist."""
    existing_count = db.query(AestheticRoom).count()
    if existing_count > 0:
        return 0

    seeded_count = 0
    for room_data in DEFAULT_ROOMS:
        room = AestheticRoom(**room_data)
        db.add(room)
        seeded_count += 1

    db.commit()
    return seeded_count
