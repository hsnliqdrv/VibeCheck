"""
Integration tests for the Resend email integration.

These tests run against a live backend (Docker) and verify that the
email-sending code paths do not break the API endpoints. Actual email
delivery is confirmed via the Resend dashboard, not in these tests.

Requires:
    - Backend running at localhost:3000 (docker compose up)
    - RESEND_API_KEY configured in backend/.env

Run with:
    pytest tests/integration/test_email_integration.py -v
"""

import os
import pytest
import requests
import random
import string
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration

BASE_URL = "http://localhost:3000/api/v1"


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _rand(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _verify_email_in_db(email: str):
    """Directly mark a user as verified in the database."""
    db_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("DB_URL")
        or "postgresql://postgres:postgres@localhost:5433/vibecheck"
    )
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE users SET email_verified = true WHERE email = :email"),
            {"email": email},
        )


def _register_user(email=None, username=None, password="Test123456!"):
    """Register a new user and return the response."""
    suffix = _rand()
    email = email or f"em_{suffix}@test.com"
    username = username or f"em_{suffix}"
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
    })
    return r, email, username


def _register_verify_login(password="Test123456!"):
    """Register, verify via DB, login. Returns (token, email, username)."""
    r, email, username = _register_user(password=password)
    assert r.status_code == 201
    _verify_email_in_db(email)
    r_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email, "password": password,
    })
    assert r_login.status_code == 200
    token = r_login.json().get("token")
    return token, email, username


# ══════════════════════════════════════════════════════════════
# 1. Registration triggers verification email
# ══════════════════════════════════════════════════════════════

class TestRegistrationEmail:
    """Verify /auth/register sends a verification email without errors."""

    def test_register_returns_201(self):
        """Registration should succeed (201) even though it now sends a real email."""
        r, email, _ = _register_user()
        assert r.status_code == 201

    def test_register_response_has_email_required_flag(self):
        r, _, _ = _register_user()
        data = r.json()
        assert data["emailVerificationRequired"] is True

    def test_register_does_not_issue_jwt(self):
        r, _, _ = _register_user()
        data = r.json()
        assert "token" not in data

    def test_register_user_is_unverified(self):
        r, _, _ = _register_user()
        data = r.json()
        assert data["user"]["emailVerified"] is False

    def test_register_message_mentions_email(self):
        r, _, _ = _register_user()
        data = r.json()
        assert "email" in data["message"].lower()

    def test_duplicate_email_still_returns_409(self):
        """Even with Resend wired in, duplicate detection should work."""
        email = f"dup_{_rand()}@test.com"
        r1, _, _ = _register_user(email=email, username=f"dup1_{_rand()}")
        assert r1.status_code == 201

        r2 = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "username": f"dup2_{_rand()}",
            "password": "Test123456!",
        })
        assert r2.status_code == 409

    def test_invalid_email_still_returns_400(self):
        """Validation should run before any email-sending attempt."""
        r = requests.post(f"{BASE_URL}/auth/register", json={
            "email": "not-an-email",
            "username": f"inv_{_rand()}",
            "password": "Test123456!",
        })
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════
# 2. Forgot-password triggers reset email
# ══════════════════════════════════════════════════════════════

class TestForgotPasswordEmail:
    """Verify /auth/forgot-password sends a reset email without errors."""

    def test_forgot_password_returns_200(self):
        """Should return 200 for a verified user (real email sent)."""
        _, email, _ = _register_verify_login()
        r = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "email": email,
        })
        assert r.status_code == 200

    def test_forgot_password_generic_message(self):
        """Response should not reveal whether the email exists."""
        _, email, _ = _register_verify_login()
        r_exists = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "email": email,
        })
        r_fake = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "email": f"fake_{_rand()}@nowhere.com",
        })
        assert r_exists.json()["message"] == r_fake.json()["message"]

    def test_forgot_password_nonexistent_email_no_error(self):
        """Non-existent emails should still return 200 (no 500)."""
        r = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "email": f"ghost_{_rand()}@test.com",
        })
        assert r.status_code == 200

    def test_forgot_password_unverified_user_no_error(self):
        """Unverified user should get 200 but no email sent (no crash)."""
        r_reg, email, _ = _register_user()
        assert r_reg.status_code == 201

        r = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "email": email,
        })
        assert r.status_code == 200

    def test_forgot_password_missing_email_returns_400(self):
        r = requests.post(f"{BASE_URL}/auth/forgot-password", json={})
        assert r.status_code == 400

    def test_forgot_password_invalid_email_returns_400(self):
        r = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "email": "bad-format",
        })
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════
# 3. Full flow: register → verify → login → reset → login
# ══════════════════════════════════════════════════════════════

class TestFullEmailFlow:
    """End-to-end flow combining email-related endpoints."""

    def test_register_verify_login_reset_login(self):
        """Complete lifecycle: register, verify (DB), login, forgot-password,
        reset-password (via DB token), login with new password."""
        password = "Original1!"
        new_password = "Changed99X"

        r_reg, email, username = _register_user(password=password)
        assert r_reg.status_code == 201

        _verify_email_in_db(email)

        r_login = requests.post(f"{BASE_URL}/auth/login", json={
            "email": email, "password": password,
        })
        assert r_login.status_code == 200
        assert "token" in r_login.json()

        r_forgot = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "email": email,
        })
        assert r_forgot.status_code == 200

        db_url = (
            os.getenv("DATABASE_URL")
            or os.getenv("DB_URL")
            or "postgresql://postgres:postgres@localhost:5433/vibecheck"
        )
        engine = create_engine(db_url)
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT reset_token FROM users WHERE email = :email"),
                {"email": email},
            ).fetchone()
        assert row is not None
        assert row[0] is not None

        import secrets, hashlib
        raw_token = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(raw_token.encode()).hexdigest()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE users
                    SET reset_token = :token, reset_token_used = false,
                        reset_token_expiry = NOW() + interval '1 hour'
                    WHERE email = :email
                """),
                {"token": hashed, "email": email},
            )

        r_reset = requests.post(f"{BASE_URL}/auth/reset-password", json={
            "token": raw_token,
            "newPassword": new_password,
        })
        assert r_reset.status_code == 200

        r_old = requests.post(f"{BASE_URL}/auth/login", json={
            "email": email, "password": password,
        })
        assert r_old.status_code == 401

        r_new = requests.post(f"{BASE_URL}/auth/login", json={
            "email": email, "password": new_password,
        })
        assert r_new.status_code == 200
        assert "token" in r_new.json()

    def test_login_blocked_until_verified(self):
        """A freshly registered user cannot login until email is verified."""
        _, email, _ = _register_user()

        r = requests.post(f"{BASE_URL}/auth/login", json={
            "email": email, "password": "Test123456!",
        })
        assert r.status_code == 403

        _verify_email_in_db(email)

        r2 = requests.post(f"{BASE_URL}/auth/login", json={
            "email": email, "password": "Test123456!",
        })
        assert r2.status_code == 200
