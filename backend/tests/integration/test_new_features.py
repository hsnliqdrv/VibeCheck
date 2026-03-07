"""
Tests for the two new backend features:
  Task 1 – Aura inference (auto aesthetic tags + colors)
  Task 2 – Aesthetic rooms (CRUD, join/leave, room posts)

These are integration tests that call a running server at localhost:3000.

Run with:
    pytest tests/test_new_features.py -v
"""

import pytest
import requests
import random
import string

pytestmark = pytest.mark.integration

BASE_URL = "http://localhost:3000/api/v1"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _rand(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _verify_email(email: str):
    import os
    from sqlalchemy import create_engine, text
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "postgresql://postgres:postgres@localhost:5433/vibecheck"
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET email_verified = true WHERE email = :email"), {"email": email})

def _register_and_login() -> tuple[str, str]:
    """Create a fresh user and return (token, user_id)."""
    suffix = _rand()
    email = f"feat_{suffix}@test.com"
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "username": f"feat_{suffix}",
        "password": "Test123456!",
    })
    assert r.status_code == 201, f"Registration failed: {r.text}"
    _verify_email(email)

    r_login = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": "Test123456!"})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    data = r_login.json()
    token = data.get("token") or data.get("access_token") or data.get("accessToken")
    user_id = (data.get("userId")
               or data.get("user_id")
               or (data.get("user") or {}).get("userId"))
    assert token and user_id
    return token, user_id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def user():
    """Shared authenticated user for the whole module."""
    token, uid = _register_and_login()
    return {"token": token, "user_id": uid}


@pytest.fixture(scope="module")
def second_user():
    """A second user for multi-user scenarios."""
    token, uid = _register_and_login()
    return {"token": token, "user_id": uid}


# =============================================================
# TASK 1 — Aura inference
# =============================================================

class TestAuraInferenceTrigger:
    """Aura colors / tags should be populated automatically after shares."""

    def test_share_triggers_aura_colors(self, user):
        """After creating a share with a dominantColor, aura profile should
        contain that color."""
        color = "#FF6B9D"
        r = requests.post(f"{BASE_URL}/aura/shares", headers=_auth(user["token"]), json={
            "category": "cinema",
            "contentId": f"tt_{_rand()}",
            "title": "Test Movie",
            "image": "https://example.com/img.jpg",
            "dominantColor": color,
        })
        assert r.status_code == 201

        # Fetch aura profile
        r2 = requests.get(f"{BASE_URL}/aura/profile", headers=_auth(user["token"]))
        assert r2.status_code == 200
        data = r2.json()
        assert "auraColors" in data
        assert isinstance(data["auraColors"], list)
        # The exact color (uppercased) must appear
        assert color.upper() in [c.upper() for c in data["auraColors"]]

    def test_share_triggers_aesthetic_tags(self, user):
        """After sharing cinema content, aesthetic_tags should include
        cinema-related tags."""
        r = requests.post(f"{BASE_URL}/aura/shares", headers=_auth(user["token"]), json={
            "category": "cinema",
            "contentId": f"tt_{_rand()}",
            "title": "Arthouse Film",
            "image": "https://example.com/img.jpg",
            "dominantColor": "#112233",
        })
        assert r.status_code == 201

        r2 = requests.get(f"{BASE_URL}/aura/profile", headers=_auth(user["token"]))
        data = r2.json()
        assert "aestheticTags" in data
        tags = data["aestheticTags"]
        assert isinstance(tags, list)
        assert len(tags) > 0
        # cinema mapping produces tags like "film noir", "arthouse", etc.
        cinema_tags = {"film noir", "arthouse", "cinephile", "visual storytelling"}
        assert any(t in cinema_tags for t in tags)

    def test_post_triggers_aura_inference(self, user):
        """Creating a community post should also recompute the aura."""
        r = requests.post(f"{BASE_URL}/social/posts", headers=_auth(user["token"]), json={
            "category": "music",
            "title": "Great Album",
            "image": "https://example.com/album.jpg",
            "dominantColor": "#AABB00",
        })
        assert r.status_code == 201

        r2 = requests.get(f"{BASE_URL}/aura/profile", headers=_auth(user["token"]))
        data = r2.json()
        colors = [c.upper() for c in data.get("auraColors", [])]
        assert "#AABB00" in colors

    def test_aura_colors_max_5(self, user):
        """No matter how many shares, auraColors should have at most 5."""
        # Create several shares with distinct colors
        for i in range(7):
            hex_part = format(i * 30 + 10, '02X')
            requests.post(f"{BASE_URL}/aura/shares", headers=_auth(user["token"]), json={
                "category": "games",
                "contentId": f"g_{_rand()}",
                "title": f"Game {i}",
                "image": "https://example.com/img.jpg",
                "dominantColor": f"#{hex_part}{hex_part}{hex_part}",
            })

        r = requests.get(f"{BASE_URL}/aura/profile", headers=_auth(user["token"]))
        assert len(r.json().get("auraColors", [])) <= 5

    def test_aesthetic_tags_max_10(self, user):
        """aestheticTags list should never exceed 10 entries."""
        r = requests.get(f"{BASE_URL}/aura/profile", headers=_auth(user["token"]))
        tags = r.json().get("aestheticTags", [])
        assert len(tags) <= 10


class TestAuraProfileBlockManualTags:
    """PUT /aura/profile must reject manual aestheticTags."""

    def test_put_aesthetic_tags_returns_403(self, user):
        r = requests.put(f"{BASE_URL}/aura/profile", headers=_auth(user["token"]), json={
            "aestheticTags": ["hacker", "neon"]
        })
        assert r.status_code == 403

    def test_put_aura_colors_still_works(self, user):
        """Users may still manually set auraColors via PUT."""
        r = requests.put(f"{BASE_URL}/aura/profile", headers=_auth(user["token"]), json={
            "auraColors": ["#111111", "#222222"]
        })
        assert r.status_code == 200

    def test_put_invalid_color_rejected(self, user):
        r = requests.put(f"{BASE_URL}/aura/profile", headers=_auth(user["token"]), json={
            "auraColors": ["not-a-color"]
        })
        assert r.status_code == 400


# =============================================================
# TASK 2 — Aesthetic Rooms
# =============================================================

class TestGetRooms:
    """GET /social/rooms"""

    def test_get_rooms_200(self):
        r = requests.get(f"{BASE_URL}/social/rooms")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    def test_get_rooms_pagination(self):
        r = requests.get(f"{BASE_URL}/social/rooms?limit=5&offset=0")
        assert r.status_code == 200
        data = r.json()
        assert data["limit"] == 5
        assert data["offset"] == 0

    def test_get_rooms_trending_filter(self):
        r = requests.get(f"{BASE_URL}/social/rooms?trending=true")
        assert r.status_code == 200


class TestGetRoomById:
    """GET /social/rooms/{roomId}"""

    def test_nonexistent_room_404(self):
        r = requests.get(f"{BASE_URL}/social/rooms/nonexistent_id")
        assert r.status_code == 404


class TestJoinLeaveRoom:
    """POST /social/rooms/{roomId}/join and /leave"""

    @pytest.fixture(autouse=True)
    def _setup_room(self, user):
        """Create a room directly through the DB isn't possible via API yet,
        so we'll use whatever rooms exist.  If none exist, skip."""
        r = requests.get(f"{BASE_URL}/social/rooms")
        rooms = r.json().get("data", [])
        if rooms:
            self.room_id = rooms[0]["id"]
            self.skip = False
        else:
            self.room_id = None
            self.skip = True

    def test_join_room(self, user):
        if self.skip:
            pytest.skip("No rooms available to test join")
        r = requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/join",
            headers=_auth(user["token"]),
        )
        assert r.status_code == 200
        data = r.json()
        assert "memberCount" in data
        assert data["memberCount"] >= 1

    def test_join_room_idempotent(self, user):
        """Joining the same room twice should succeed silently."""
        if self.skip:
            pytest.skip("No rooms available")
        r1 = requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/join",
            headers=_auth(user["token"]),
        )
        count1 = r1.json()["memberCount"]
        r2 = requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/join",
            headers=_auth(user["token"]),
        )
        count2 = r2.json()["memberCount"]
        assert count1 == count2  # no double-counting

    def test_leave_room(self, user):
        if self.skip:
            pytest.skip("No rooms available")
        # Make sure we're a member first
        requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/join",
            headers=_auth(user["token"]),
        )
        r = requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/leave",
            headers=_auth(user["token"]),
        )
        assert r.status_code == 204

    def test_join_nonexistent_room_404(self, user):
        r = requests.post(
            f"{BASE_URL}/social/rooms/nonexistent_id/join",
            headers=_auth(user["token"]),
        )
        assert r.status_code == 404

    def test_leave_nonexistent_room_404(self, user):
        r = requests.post(
            f"{BASE_URL}/social/rooms/nonexistent_id/leave",
            headers=_auth(user["token"]),
        )
        assert r.status_code == 404

    def test_join_requires_auth(self):
        r = requests.post(f"{BASE_URL}/social/rooms/some_id/join")
        assert r.status_code == 401

    def test_leave_requires_auth(self):
        r = requests.post(f"{BASE_URL}/social/rooms/some_id/leave")
        assert r.status_code == 401


class TestRoomPosts:
    """GET and POST /social/rooms/{roomId}/posts"""

    @pytest.fixture(autouse=True)
    def _setup_room(self, user):
        r = requests.get(f"{BASE_URL}/social/rooms")
        rooms = r.json().get("data", [])
        if rooms:
            self.room_id = rooms[0]["id"]
            self.skip = False
            # Ensure user is a member
            requests.post(
                f"{BASE_URL}/social/rooms/{self.room_id}/join",
                headers=_auth(user["token"]),
            )
        else:
            self.room_id = None
            self.skip = True

    def test_get_room_posts_empty_or_list(self, user):
        if self.skip:
            pytest.skip("No rooms available")
        r = requests.get(f"{BASE_URL}/social/rooms/{self.room_id}/posts")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_create_room_post(self, user):
        if self.skip:
            pytest.skip("No rooms available")
        r = requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/posts",
            headers=_auth(user["token"]),
            json={
                "category": "cinema",
                "title": "Room post test",
                "image": "https://example.com/img.jpg",
                "dominantColor": "#ABCDEF",
            },
        )
        assert r.status_code == 201
        post = r.json().get("post", {})
        assert post.get("roomId") == self.room_id

    def test_create_room_post_missing_fields(self, user):
        if self.skip:
            pytest.skip("No rooms available")
        r = requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/posts",
            headers=_auth(user["token"]),
            json={"category": "cinema"},
        )
        assert r.status_code == 400

    def test_create_room_post_invalid_category(self, user):
        if self.skip:
            pytest.skip("No rooms available")
        r = requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/posts",
            headers=_auth(user["token"]),
            json={
                "category": "invalid",
                "title": "Bad category",
                "image": "https://example.com/img.jpg",
            },
        )
        assert r.status_code == 400

    def test_create_post_nonexistent_room_404(self, user):
        r = requests.post(
            f"{BASE_URL}/social/rooms/nonexistent_id/posts",
            headers=_auth(user["token"]),
            json={
                "category": "cinema",
                "title": "Should fail",
                "image": "https://example.com/img.jpg",
            },
        )
        assert r.status_code == 404

    def test_room_post_count_incremented(self, user):
        """After posting, the room's postCount should increase."""
        if self.skip:
            pytest.skip("No rooms available")
        # Get current count
        r1 = requests.get(f"{BASE_URL}/social/rooms/{self.room_id}")
        before = r1.json().get("postCount", 0)

        # Create a post
        requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/posts",
            headers=_auth(user["token"]),
            json={
                "category": "books",
                "title": "Room count test",
                "image": "https://example.com/img.jpg",
            },
        )

        r2 = requests.get(f"{BASE_URL}/social/rooms/{self.room_id}")
        after = r2.json().get("postCount", 0)
        assert after == before + 1

    def test_room_post_appears_in_room_feed(self, user):
        """A post created in a room should show up in GET /rooms/{id}/posts."""
        if self.skip:
            pytest.skip("No rooms available")
        r = requests.post(
            f"{BASE_URL}/social/rooms/{self.room_id}/posts",
            headers=_auth(user["token"]),
            json={
                "category": "travel",
                "title": f"Visible-{_rand()}",
                "image": "https://example.com/img.jpg",
            },
        )
        post_id = r.json()["post"]["id"]

        r2 = requests.get(f"{BASE_URL}/social/rooms/{self.room_id}/posts")
        ids = [p["id"] for p in r2.json()["data"]]
        assert post_id in ids

    def test_room_post_requires_auth(self):
        r = requests.post(
            f"{BASE_URL}/social/rooms/some_id/posts",
            json={
                "category": "cinema",
                "title": "No auth",
                "image": "https://example.com/img.jpg",
            },
        )
        assert r.status_code == 401


class TestPostIncludesRoomId:
    """The general post creation should optionally accept roomId and return it."""

    def test_global_post_has_null_room_id(self, user):
        r = requests.post(f"{BASE_URL}/social/posts", headers=_auth(user["token"]), json={
            "category": "cinema",
            "title": "Global post",
            "image": "https://example.com/img.jpg",
        })
        assert r.status_code == 201
        assert r.json()["post"].get("roomId") is None


# =============================================================
# ADDITIONAL COVERAGE — regression-proof tests
# =============================================================

class TestCrossCategoryAestheticTags:
    """Sharing across multiple categories should produce tags from each."""

    def test_multi_category_tags(self):
        """A user who shares cinema AND music content should have tags from
        both categories in their aura profile."""
        token, uid = _register_and_login()
        headers = _auth(token)

        # Share cinema content
        r1 = requests.post(f"{BASE_URL}/aura/shares", headers=headers, json={
            "category": "cinema",
            "contentId": f"tt_{_rand()}",
            "title": "Blade Runner 2049",
            "image": "https://example.com/blade.jpg",
            "dominantColor": "#1A1A2E",
        })
        assert r1.status_code == 201

        # Share music content
        r2 = requests.post(f"{BASE_URL}/aura/shares", headers=headers, json={
            "category": "music",
            "contentId": f"sp_{_rand()}",
            "title": "Dark Side of the Moon",
            "image": "https://example.com/dsotm.jpg",
            "dominantColor": "#0D0D0D",
        })
        assert r2.status_code == 201

        # Fetch profile and check tags from BOTH categories
        r3 = requests.get(f"{BASE_URL}/aura/profile", headers=headers)
        assert r3.status_code == 200
        tags = r3.json().get("aestheticTags", [])
        cinema_tags = {"film noir", "arthouse", "cinephile", "visual storytelling"}
        music_tags = {"audiophile", "sonic explorer", "melodic", "vinyl culture"}
        has_cinema = any(t in cinema_tags for t in tags)
        has_music = any(t in music_tags for t in tags)
        assert has_cinema, f"Expected cinema tags but got: {tags}"
        assert has_music, f"Expected music tags but got: {tags}"


class TestColorDeduplication:
    """Sharing the same color many times should not create duplicates in aura."""

    def test_same_color_deduped(self):
        token, uid = _register_and_login()
        headers = _auth(token)

        # Share 5 items all with the exact same dominant color
        for i in range(5):
            requests.post(f"{BASE_URL}/aura/shares", headers=headers, json={
                "category": "books",
                "contentId": f"bk_{_rand()}",
                "title": f"Book {i}",
                "image": "https://example.com/img.jpg",
                "dominantColor": "#FF0000",
            })

        r = requests.get(f"{BASE_URL}/aura/profile", headers=headers)
        colors = r.json().get("auraColors", [])
        # The color should appear at most once (no duplicates)
        upper_colors = [c.upper() for c in colors]
        assert upper_colors.count("#FF0000") <= 1, \
            f"Color #FF0000 duplicated: {colors}"
        # But it SHOULD appear
        assert "#FF0000" in upper_colors, f"Expected #FF0000 in {colors}"

    def test_similar_colors_deduped(self):
        """Colors that are perceptually very close should be de-duplicated."""
        token, uid = _register_and_login()
        headers = _auth(token)

        # Share items with near-identical colors (differ by ~1-2 in each channel)
        similar = ["#FF0000", "#FF0101", "#FE0000", "#FF0100", "#FE0101"]
        for i, color in enumerate(similar):
            requests.post(f"{BASE_URL}/aura/shares", headers=headers, json={
                "category": "cinema",
                "contentId": f"tt_{_rand()}",
                "title": f"Similar {i}",
                "image": "https://example.com/img.jpg",
                "dominantColor": color,
            })

        r = requests.get(f"{BASE_URL}/aura/profile", headers=headers)
        colors = r.json().get("auraColors", [])
        # De-duplication should reduce these very similar colors
        assert len(colors) < len(similar), \
            f"Expected de-duplication to reduce {len(similar)} similar colors, got {len(colors)}: {colors}"


class TestRoomPostTriggersInference:
    """Creating a post inside a room should also trigger aura inference."""

    def test_room_post_updates_aura(self):
        token, uid = _register_and_login()
        headers = _auth(token)

        # Get a room
        r = requests.get(f"{BASE_URL}/social/rooms")
        rooms = r.json().get("data", [])
        if not rooms:
            pytest.skip("No rooms available")

        room_id = rooms[0]["id"]
        requests.post(f"{BASE_URL}/social/rooms/{room_id}/join", headers=headers)

        # Create a room post with a distinct color
        color = "#00FF99"
        r2 = requests.post(
            f"{BASE_URL}/social/rooms/{room_id}/posts",
            headers=headers,
            json={
                "category": "travel",
                "title": "Room inference test",
                "image": "https://example.com/img.jpg",
                "dominantColor": color,
            },
        )
        assert r2.status_code == 201

        # Check that the color appears in the user's aura profile
        r3 = requests.get(f"{BASE_URL}/aura/profile", headers=headers)
        assert r3.status_code == 200
        colors = [c.upper() for c in r3.json().get("auraColors", [])]
        assert color.upper() in colors, \
            f"Room post color {color} missing from aura: {colors}"


class TestAuraInferenceIdempotent:
    """Calling inference multiple times should produce stable results,
    not accumulate unbounded data."""

    def test_repeated_shares_stable_profile(self):
        token, uid = _register_and_login()
        headers = _auth(token)

        # Create 3 shares
        for i in range(3):
            hex_part = format(50 + i * 60, '02X')
            requests.post(f"{BASE_URL}/aura/shares", headers=headers, json={
                "category": "games",
                "contentId": f"g_{_rand()}",
                "title": f"Game {i}",
                "image": "https://example.com/img.jpg",
                "dominantColor": f"#{hex_part}00{hex_part}",
            })

        # Read profile twice — should be identical both times
        r1 = requests.get(f"{BASE_URL}/aura/profile", headers=headers)
        r2 = requests.get(f"{BASE_URL}/aura/profile", headers=headers)
        assert r1.json()["auraColors"] == r2.json()["auraColors"]
        assert r1.json()["aestheticTags"] == r2.json()["aestheticTags"]


class TestLeaveRoomDecrementsMemberCount:
    """Leaving a room should decrement the member count (not go negative)."""

    def test_leave_decrements_count(self):
        token, uid = _register_and_login()
        headers = _auth(token)

        r = requests.get(f"{BASE_URL}/social/rooms")
        rooms = r.json().get("data", [])
        if not rooms:
            pytest.skip("No rooms available")
        room_id = rooms[0]["id"]

        # Join
        rj = requests.post(f"{BASE_URL}/social/rooms/{room_id}/join", headers=headers)
        assert rj.status_code == 200
        count_after_join = rj.json()["memberCount"]

        # Leave
        rl = requests.post(f"{BASE_URL}/social/rooms/{room_id}/leave", headers=headers)
        assert rl.status_code == 204

        # Verify count went down
        rr = requests.get(f"{BASE_URL}/social/rooms/{room_id}")
        assert rr.status_code == 200
        count_after_leave = rr.json()["memberCount"]
        assert count_after_leave == count_after_join - 1

    def test_leave_without_join_no_negative(self):
        """Leaving a room you never joined should not make count negative."""
        token, uid = _register_and_login()
        headers = _auth(token)

        r = requests.get(f"{BASE_URL}/social/rooms")
        rooms = r.json().get("data", [])
        if not rooms:
            pytest.skip("No rooms available")
        room_id = rooms[0]["id"]

        r1 = requests.get(f"{BASE_URL}/social/rooms/{room_id}")
        count_before = r1.json()["memberCount"]

        # Leave without joining
        requests.post(f"{BASE_URL}/social/rooms/{room_id}/leave", headers=headers)

        r2 = requests.get(f"{BASE_URL}/social/rooms/{room_id}")
        count_after = r2.json()["memberCount"]
        assert count_after == count_before  # unchanged
        assert count_after >= 0  # never negative
