import random


def generate_random_avatar_url() -> str:
    """Return a random avatar URL using the same CDN pattern as new users."""
    avatar_index = random.randint(1, 27)
    return f"https://cdn.jsdelivr.net/gh/alohe/avatars/png/vibrent_{avatar_index}.png"