"""
Badges & Gamification Test Suite
Tests all 6 endpoints:
  GET /badges
  GET /badges/user              (JWT required)
  GET /badges/user/{userId}
  GET /curator/stats            (JWT required)
  GET /curator/stats/{userId}
  GET /curator/levels

Run with:
    pytest tests/test_badges.py -v
"""

import pytest
import requests
import random
import string

BASE_URL = "http://localhost:3000/api/v1"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def random_suffix(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def register_and_login() -> tuple[str, str]:
    """Create a fresh user and return (token, user_id)."""
    suffix = random_suffix()
    payload = {
        "email": f"badge_test_{suffix}@test.com",
        "username": f"badger_{suffix}",
        "password": "Test123456!",
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=payload)
    assert r.status_code == 201, f"Registration failed: {r.text}"
    data = r.json()
    token = data.get("token") or data.get("access_token") or data.get("accessToken")
    user_id = data.get("userId") or data.get("user_id") or (data.get("user") or {}).get("userId")
    assert token, f"No token in register response: {data}"
    assert user_id, f"No userId in register response: {data}"
    return token, user_id


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def user_credentials():
    """Single user shared across the module tests."""
    return register_and_login()


@pytest.fixture(scope="module")
def token(user_credentials):
    return user_credentials[0]


@pytest.fixture(scope="module")
def user_id(user_credentials):
    return user_credentials[1]


# ─────────────────────────────────────────────
# GET /badges
# ─────────────────────────────────────────────

class TestGetAllBadges:
    def test_returns_200(self):
        r = requests.get(f"{BASE_URL}/badges")
        assert r.status_code == 200

    def test_response_shape(self):
        r = requests.get(f"{BASE_URL}/badges")
        data = r.json()
        assert "badges" in data
        assert "total" in data
        assert isinstance(data["badges"], list)
        assert data["total"] == len(data["badges"])

    def test_badges_seeded(self):
        """At least 14 default badges should exist after seeding."""
        r = requests.get(f"{BASE_URL}/badges")
        data = r.json()
        assert data["total"] >= 14, f"Expected >=14 badges, got {data['total']}"

    def test_badge_fields(self):
        r = requests.get(f"{BASE_URL}/badges")
        badges = r.json()["badges"]
        required = {"id", "name", "description", "icon", "rarity", "category", "maxProgress", "unlocked", "progress"}
        for badge in badges:
            missing = required - badge.keys()
            assert not missing, f"Badge '{badge.get('name')}' missing fields: {missing}"

    def test_filter_by_rarity(self):
        for rarity in ["common", "rare", "epic", "legendary"]:
            r = requests.get(f"{BASE_URL}/badges", params={"rarity": rarity})
            assert r.status_code == 200, f"rarity={rarity} failed"
            badges = r.json()["badges"]
            for b in badges:
                assert b["rarity"] == rarity, f"Unexpected rarity {b['rarity']}"

    def test_filter_by_category(self):
        for cat in ["early", "completionist", "social", "streak", "special"]:
            r = requests.get(f"{BASE_URL}/badges", params={"category": cat})
            assert r.status_code == 200, f"category={cat} failed"
            badges = r.json()["badges"]
            for b in badges:
                assert b["category"] == cat

    def test_invalid_rarity_returns_400(self):
        r = requests.get(f"{BASE_URL}/badges", params={"rarity": "mythic"})
        assert r.status_code == 400

    def test_invalid_category_returns_400(self):
        r = requests.get(f"{BASE_URL}/badges", params={"category": "nonsense"})
        assert r.status_code == 400


# ─────────────────────────────────────────────
# GET /badges/user  (JWT required)
# ─────────────────────────────────────────────

class TestGetCurrentUserBadges:
    def test_requires_auth(self):
        r = requests.get(f"{BASE_URL}/badges/user")
        assert r.status_code == 401

    def test_returns_200_with_auth(self, token):
        r = requests.get(f"{BASE_URL}/badges/user", headers=auth_header(token))
        assert r.status_code == 200

    def test_response_shape(self, token):
        r = requests.get(f"{BASE_URL}/badges/user", headers=auth_header(token))
        data = r.json()
        assert "badges" in data
        assert "earnedCount" in data
        assert "totalCount" in data

    def test_total_matches_badge_catalog(self, token):
        """totalCount should equal the number of badges in the catalog."""
        all_r = requests.get(f"{BASE_URL}/badges")
        user_r = requests.get(f"{BASE_URL}/badges/user", headers=auth_header(token))
        assert user_r.json()["totalCount"] == all_r.json()["total"]

    def test_new_user_has_no_share_dependent_badges(self, token):
        r = requests.get(f"{BASE_URL}/badges/user", headers=auth_header(token))
        data = r.json()
        # Share-dependent badges (Film Buff, 7-Day Streak, etc.) must not be
        # unlocked for a brand-new user with zero shares.
        # Note: "Early Adopter" is intentionally auto-unlocked for beta users.
        share_dependent = {
            "Film Buff", "Audiophile", "Bookworm", "Gamer", "Wanderer",
            "All-Rounder", "Social Butterfly", "Trendsetter",
            "7-Day Streak", "30-Day Streak", "Tastemaker", "Legend",
        }
        for badge in data["badges"]:
            if badge["name"] in share_dependent:
                assert not badge["unlocked"], (
                    f"Badge '{badge['name']}' should not be unlocked for a new user"
                )

    def test_badge_progress_fields(self, token):
        r = requests.get(f"{BASE_URL}/badges/user", headers=auth_header(token))
        for b in r.json()["badges"]:
            assert "progress" in b
            assert "maxProgress" in b
            assert "unlocked" in b
            assert isinstance(b["unlocked"], bool)


# ─────────────────────────────────────────────
# GET /badges/user/{userId}
# ─────────────────────────────────────────────

class TestGetUserBadgesById:
    def test_valid_user(self, user_id):
        r = requests.get(f"{BASE_URL}/badges/user/{user_id}")
        assert r.status_code == 200

    def test_response_includes_username(self, user_id):
        r = requests.get(f"{BASE_URL}/badges/user/{user_id}")
        data = r.json()
        assert "userId" in data
        assert "username" in data
        assert data["userId"] == user_id

    def test_response_shape(self, user_id):
        r = requests.get(f"{BASE_URL}/badges/user/{user_id}")
        data = r.json()
        assert "badges" in data
        assert "earnedCount" in data
        assert "totalCount" in data

    def test_unknown_user_returns_404(self):
        r = requests.get(f"{BASE_URL}/badges/user/u_nonexistentXXXX")
        assert r.status_code == 404


# ─────────────────────────────────────────────
# GET /curator/stats  (JWT required)
# ─────────────────────────────────────────────

class TestGetCuratorStats:
    def test_requires_auth(self):
        r = requests.get(f"{BASE_URL}/curator/stats")
        assert r.status_code == 401

    def test_returns_200_with_auth(self, token):
        r = requests.get(f"{BASE_URL}/curator/stats", headers=auth_header(token))
        assert r.status_code == 200

    def test_response_fields(self, token):
        r = requests.get(f"{BASE_URL}/curator/stats", headers=auth_header(token))
        data = r.json()
        required = {
            "userId", "username", "totalShares", "totalXP",
            "currentLevel", "currentLevelName", "xpToNextLevel",
            "streakDays", "categoryBreakdown", "badges", "badgeCount",
        }
        missing = required - data.keys()
        assert not missing, f"Missing fields: {missing}"

    def test_new_user_starts_at_level_1(self, token):
        r = requests.get(f"{BASE_URL}/curator/stats", headers=auth_header(token))
        data = r.json()
        assert data["currentLevel"] == 1
        assert data["totalShares"] == 0
        assert data["totalXP"] == 0

    def test_xp_calculation_after_share(self, token, user_id):
        """Create a share then verify XP goes up by 10."""
        # First, get a real content id from the movies endpoint
        movies_r = requests.get(f"{BASE_URL}/content/movies", params={"limit": 1})
        movie_id = None
        if movies_r.status_code == 200 and movies_r.json().get("movies"):
            movie_id = movies_r.json()["movies"][0]["id"]

        share_payload = {
            "category": "cinema",
            "contentId": movie_id or "tt0111161",
            "title": "Test Movie Share",
            "caption": "badge test share",
        }
        share_r = requests.post(
            f"{BASE_URL}/aura/shares",
            json=share_payload,
            headers=auth_header(token),
        )
        if share_r.status_code not in (200, 201):
            pytest.skip(f"Share creation returned {share_r.status_code}; skipping XP test")

        stats_r = requests.get(f"{BASE_URL}/curator/stats", headers=auth_header(token))
        data = stats_r.json()
        assert data["totalShares"] >= 1
        assert data["totalXP"] >= 10

    def test_streak_days_is_integer(self, token):
        r = requests.get(f"{BASE_URL}/curator/stats", headers=auth_header(token))
        assert isinstance(r.json()["streakDays"], int)


# ─────────────────────────────────────────────
# GET /curator/stats/{userId}
# ─────────────────────────────────────────────

class TestGetCuratorStatsByUserId:
    def test_valid_user(self, user_id):
        r = requests.get(f"{BASE_URL}/curator/stats/{user_id}")
        assert r.status_code == 200

    def test_response_has_all_fields(self, user_id):
        r = requests.get(f"{BASE_URL}/curator/stats/{user_id}")
        data = r.json()
        required = {"userId", "username", "totalShares", "totalXP", "currentLevel"}
        missing = required - data.keys()
        assert not missing, f"Missing fields: {missing}"

    def test_user_id_matches(self, user_id):
        r = requests.get(f"{BASE_URL}/curator/stats/{user_id}")
        assert r.json()["userId"] == user_id

    def test_unknown_user_returns_404(self):
        r = requests.get(f"{BASE_URL}/curator/stats/u_nonexistentXXXX")
        assert r.status_code == 404


# ─────────────────────────────────────────────
# GET /curator/levels
# ─────────────────────────────────────────────

class TestGetCuratorLevels:
    def test_returns_200(self):
        r = requests.get(f"{BASE_URL}/curator/levels")
        assert r.status_code == 200

    def test_response_shape(self):
        r = requests.get(f"{BASE_URL}/curator/levels")
        data = r.json()
        assert "levels" in data
        assert "total" in data
        assert isinstance(data["levels"], list)

    def test_ten_levels_seeded(self):
        r = requests.get(f"{BASE_URL}/curator/levels")
        data = r.json()
        assert data["total"] == 10, f"Expected 10 levels, got {data['total']}"

    def test_level_fields(self):
        r = requests.get(f"{BASE_URL}/curator/levels")
        for lvl in r.json()["levels"]:
            assert "level" in lvl
            assert "name" in lvl
            assert "xpRequired" in lvl
            assert "rewards" in lvl
            assert "color" in lvl
            assert isinstance(lvl["rewards"], list)

    def test_levels_ordered_ascending(self):
        r = requests.get(f"{BASE_URL}/curator/levels")
        levels = r.json()["levels"]
        nums = [l["level"] for l in levels]
        assert nums == sorted(nums), f"Levels not sorted: {nums}"

    def test_xp_required_increases(self):
        r = requests.get(f"{BASE_URL}/curator/levels")
        levels = r.json()["levels"]
        xp_vals = [l["xpRequired"] for l in levels]
        assert xp_vals == sorted(xp_vals), f"XP not increasing: {xp_vals}"

    def test_first_level_requires_zero_xp(self):
        r = requests.get(f"{BASE_URL}/curator/levels")
        first = r.json()["levels"][0]
        assert first["xpRequired"] == 0

    def test_color_is_hex(self):
        import re
        hex_re = re.compile(r"^#[0-9A-Fa-f]{6}$")
        r = requests.get(f"{BASE_URL}/curator/levels")
        for lvl in r.json()["levels"]:
            assert hex_re.match(lvl["color"]), f"Bad color: {lvl['color']}"
