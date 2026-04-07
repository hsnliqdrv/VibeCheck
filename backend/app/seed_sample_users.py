from typing import Dict, List

from app.models.user import User
from app.services.avatar_service import generate_random_avatar_url


SAMPLE_USERS: List[Dict[str, object]] = [
    {
        "email": "sample1@vibecheck.app",
        "username": "sample_vibes_1",
        "password": "Sample123!",
        "bio": "I collect neon cinema, late-night synth, and cozy book corners.",
        "aura_colors": ["#6B6BF8", "#B44AFF", "#FBBF24"],
        "aesthetic_tags": ["cinephile", "synthwave", "indie"],
        "social_media_links": [
            {"platform": "instagram", "url": "https://instagram.com/sample_vibes_1"}
        ],
    },
    {
        "email": "sample2@vibecheck.app",
        "username": "sample_vibes_2",
        "password": "Sample123!",
        "bio": "Books, travel journals, and rainy-day playlists.",
        "aura_colors": ["#0EA5E9", "#14B8A6", "#22C55E"],
        "aesthetic_tags": ["reader", "travelcore", "calm vibes"],
        "social_media_links": [
            {"platform": "twitter", "url": "https://x.com/sample_vibes_2"}
        ],
    },
    {
        "email": "sample3@vibecheck.app",
        "username": "sample_vibes_3",
        "password": "Sample123!",
        "bio": "Arcade nostalgia, street photography, and lo-fi mornings.",
        "aura_colors": ["#EF4444", "#F97316", "#A855F7"],
        "aesthetic_tags": ["retro gamer", "street style", "lo-fi"],
        "social_media_links": [
            {"platform": "spotify", "url": "https://open.spotify.com/user/sample_vibes_3"}
        ],
    },
]


def seed_sample_users(db) -> int:
    """Seed 3 sample users on startup if they don't already exist."""
    seeded_count = 0

    for user_data in SAMPLE_USERS:
        existing = db.query(User).filter(
            (User.email == user_data["email"]) | (User.username == user_data["username"])
        ).first()
        if existing:
            continue

        user = User(
            email=str(user_data["email"]),
            username=str(user_data["username"]),
            avatar=generate_random_avatar_url(),
            bio=str(user_data["bio"]),
            email_verified=True,
            aura_colors=user_data["aura_colors"],
            aesthetic_tags=user_data["aesthetic_tags"],
            social_media_links=user_data["social_media_links"],
        )
        user.set_password(str(user_data["password"]))

        db.add(user)
        seeded_count += 1

    if seeded_count > 0:
        db.commit()

    return seeded_count
