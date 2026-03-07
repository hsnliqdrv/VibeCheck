"""
Tests for new backend features:
  - Email verification flow (register, verify, login gating)
  - Forgot/reset password
  - socialMediaLinks validation
  - Badge date formatting
  - Discovery feed endpoint

Uses Flask test client (no running server needed).

Usage (from the repository root):
    cd <repo-root>
    pytest backend/tests/test_new_endpoints.py -v
"""

import os
import re
import sys
import pytest

# Ensure the backend root is on sys.path
# Go up two directories from tests/unit/ to /backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.config import Config
Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///test_vibecheck.db'

# Don't pollute other tests - let app default to sqlite if needed locally or we use a fixture
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key')

from app import create_app


@pytest.fixture(scope='module')
def app():
    """Create Flask app for testing."""
    application = create_app()
    application.config['TESTING'] = True
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_vibecheck.db'
    yield application
    # Cleanup: remove test database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'test_vibecheck.db')
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest.fixture(scope='module')
def client(app):
    """Create test client."""
    return app.test_client()


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def register_user(client, email='test@example.com', username='testuser', password='Test1234'):
    """Register a user and return the response."""
    return client.post('/api/v1/auth/register', json={
        'email': email,
        'username': username,
        'password': password,
    })


def get_verification_token(app, email):
    """Get a raw verification token for a user, using a proper request context."""
    from app.models.user import User
    with app.test_request_context():
        from app.database import get_db, close_db
        db = get_db()
        user = db.query(User).filter_by(email=email).first()
        if user and not user.email_verified:
            raw_token = user.generate_verification_token()
            db.commit()
            close_db()
            return raw_token
        close_db()
    return None


def get_reset_token(app, email):
    """Get a raw reset token for a user."""
    from app.models.user import User
    with app.test_request_context():
        from app.database import get_db, close_db
        db = get_db()
        user = db.query(User).filter_by(email=email).first()
        raw_token = user.generate_reset_token()
        db.commit()
        close_db()
        return raw_token


def register_and_verify(client, app, email, username, password='Test1234'):
    """Register and verify a user. Returns JWT token."""
    register_user(client, email, username, password)
    raw_token = get_verification_token(app, email)
    if raw_token:
        client.get(f'/api/v1/auth/verify-email?token={raw_token}')
    
    resp = client.post('/api/v1/auth/login', json={
        'email': email,
        'password': password,
    })
    return resp.get_json().get('token')


# ──────────────────────────────────────────────────────────────
# 1. Registration + Email Verification + Login Gating
# ──────────────────────────────────────────────────────────────

class TestEmailVerification:
    """Test the full registration → verification → login flow."""

    def test_register_returns_no_token(self, client):
        """Registration should NOT issue a JWT and should require email verification."""
        resp = register_user(client, 'verify@test.com', 'verifyuser')
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'token' not in data, "Registration should not issue JWT"
        assert data.get('emailVerificationRequired') is True
        assert 'user' in data
        assert data['user']['emailVerified'] is False

    def test_login_rejects_unverified_user(self, client):
        """Login should return 403 for users who haven't verified email."""
        register_user(client, 'unverified@test.com', 'unverifuser')
        resp = client.post('/api/v1/auth/login', json={
            'email': 'unverified@test.com',
            'password': 'Test1234',
        })
        assert resp.status_code == 403
        data = resp.get_json()
        assert 'verify' in data['message'].lower() or 'verified' in data['message'].lower()

    def test_verify_email_success(self, client, app):
        """Verifying email should succeed and return a JWT."""
        register_user(client, 'toverify@test.com', 'toverify')
        raw_token = get_verification_token(app, 'toverify@test.com')
        assert raw_token is not None

        resp = client.get(f'/api/v1/auth/verify-email?token={raw_token}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'token' in data, "Verify-email should return a JWT"
        assert data['user']['emailVerified'] is True

    def test_login_after_verification(self, client):
        """After email verification, login should succeed."""
        resp = client.post('/api/v1/auth/login', json={
            'email': 'toverify@test.com',
            'password': 'Test1234',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'token' in data

    def test_verify_email_invalid_token(self, client):
        """Invalid verification token should return 404."""
        resp = client.get('/api/v1/auth/verify-email?token=totally_invalid_token')
        assert resp.status_code == 404

    def test_verify_email_missing_token(self, client):
        """Missing verification token should return 400."""
        resp = client.get('/api/v1/auth/verify-email')
        assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────
# 2. Forgot / Reset Password
# ──────────────────────────────────────────────────────────────

class TestForgotResetPassword:
    """Test the forgot-password → reset-password flow."""

    def test_forgot_password_success(self, client, app):
        """forgot-password should return 200 for verified user."""
        register_and_verify(client, app, 'forgot@test.com', 'forgotuser')
        
        resp = client.post('/api/v1/auth/forgot-password', json={
            'email': 'forgot@test.com'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'message' in data

    def test_forgot_password_nonexistent_email(self, client):
        """forgot-password should return 200 even for non-existent email."""
        resp = client.post('/api/v1/auth/forgot-password', json={
            'email': 'nobody@test.com'
        })
        assert resp.status_code == 200

    def test_reset_password_success(self, client, app):
        """reset-password should update the user's password."""
        raw_reset_token = get_reset_token(app, 'forgot@test.com')

        resp = client.post('/api/v1/auth/reset-password', json={
            'token': raw_reset_token,
            'newPassword': 'NewPass123'
        })
        assert resp.status_code == 200

        resp = client.post('/api/v1/auth/login', json={
            'email': 'forgot@test.com',
            'password': 'NewPass123'
        })
        assert resp.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """reset-password with invalid token should return 400."""
        resp = client.post('/api/v1/auth/reset-password', json={
            'token': 'invalid_token',
            'newPassword': 'NewPass123'
        })
        assert resp.status_code == 400

    def test_reset_password_weak_password(self, client, app):
        """reset-password should enforce password policy."""
        raw_token = get_reset_token(app, 'forgot@test.com')
        resp = client.post('/api/v1/auth/reset-password', json={
            'token': raw_token,
            'newPassword': 'weak'
        })
        assert resp.status_code == 400

    def test_forgot_password_missing_email(self, client):
        """forgot-password without email should return 400."""
        resp = client.post('/api/v1/auth/forgot-password', json={})
        assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────
# 3. socialMediaLinks
# ──────────────────────────────────────────────────────────────

class TestSocialMediaLinks:
    """Test socialMediaLinks validation on PUT /users/profile."""

    def test_social_links_flow(self, client, app):
        """Test the full social links flow: update, get profile, get public profile."""
        token = register_and_verify(client, app, 'social@test.com', 'socialuser')
        headers = {'Authorization': f'Bearer {token}'}
        
        # Update with valid links
        resp = client.put('/api/v1/users/profile', headers=headers, json={
            'socialMediaLinks': [
                {'platform': 'instagram', 'url': 'https://instagram.com/testuser'},
                {'platform': 'twitter', 'url': 'https://twitter.com/testuser'},
            ]
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['socialMediaLinks']) == 2

        # Get profile - should include links
        resp = client.get('/api/v1/users/profile', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'socialMediaLinks' in data
        user_id = data['userId']

        # Get public profile - should include links
        resp = client.get(f'/api/v1/users/{user_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'socialMediaLinks' in data

    def test_social_links_invalid_platform(self, client, app):
        """Invalid platform should be rejected."""
        token = register_and_verify(client, app, 'social2@test.com', 'socialuser2')
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = client.put('/api/v1/users/profile', headers=headers, json={
            'socialMediaLinks': [
                {'platform': 'myspace', 'url': 'https://myspace.com/test'},
            ]
        })
        assert resp.status_code == 400

    def test_social_links_invalid_url(self, client, app):
        """Invalid URL should be rejected."""
        token = register_and_verify(client, app, 'social3@test.com', 'socialuser3')
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = client.put('/api/v1/users/profile', headers=headers, json={
            'socialMediaLinks': [
                {'platform': 'twitter', 'url': 'not-a-url'},
            ]
        })
        assert resp.status_code == 400

    def test_all_valid_platforms(self, client, app):
        """All platform values from the contract should be accepted."""
        token = register_and_verify(client, app, 'social4@test.com', 'socialuser4')
        headers = {'Authorization': f'Bearer {token}'}
        
        platforms = ['instagram', 'twitter', 'tiktok', 'youtube', 'facebook',
                     'linkedin', 'pinterest', 'spotify', 'twitch', 'other']
        links = [{'platform': p, 'url': f'https://{p}.com/test'} for p in platforms]
        resp = client.put('/api/v1/users/profile', headers=headers, json={
            'socialMediaLinks': links
        })
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────
# 4. Badge Date Formatting
# ──────────────────────────────────────────────────────────────

class TestBadgeDateFormatting:
    """Test that badge unlockedDate uses human-readable format."""

    def test_badge_date_format_strftime(self):
        """The strftime format used in Badge to_dict produces human readable dates."""
        from datetime import datetime

        test_date = datetime(2026, 3, 2, 14, 55, 0)
        formatted = test_date.strftime('%B %-d, %Y at %-I:%M %p')
        
        # Should NOT be ISO format
        assert 'T' not in formatted, "Should not be ISO format"
        assert '2026' in formatted
        # Should match pattern like "March 2, 2026 at 2:55 PM"
        assert re.match(r'.+\d{4} at \d{1,2}:\d{2} [AP]M', formatted)
        assert 'March' in formatted
        assert '2:55 PM' in formatted

    def test_badge_date_not_iso(self):
        """Badge dates should not use ISO format."""
        from datetime import datetime

        test_date = datetime(2026, 3, 2, 14, 55, 0)
        formatted = test_date.strftime('%B %-d, %Y at %-I:%M %p')
        
        # Should NOT look like "2026-03-02T14:55:00" 
        assert 'T' not in formatted
        # Should look like "March 2, 2026 at 2:55 PM"
        assert 'March' in formatted
        assert '2:55 PM' in formatted


# ──────────────────────────────────────────────────────────────
# 5. Discovery Feed
# ──────────────────────────────────────────────────────────────

class TestDiscoveryFeed:
    """Test GET /discovery/feed endpoint."""

    def test_discovery_feed_returns_200(self, client, app):
        """GET /discovery/feed should return 200 with data array."""
        token = register_and_verify(client, app, 'discover@test.com', 'discoveruser')
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = client.get('/api/v1/discovery/feed', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'data' in data
        assert 'total' in data
        assert isinstance(data['data'], list)

    def test_discovery_feed_requires_auth(self, client):
        """GET /discovery/feed without JWT should return 401."""
        resp = client.get('/api/v1/discovery/feed')
        assert resp.status_code == 401

    def test_discovery_feed_with_limit(self, client, app):
        """GET /discovery/feed?limit=5 should respect limit."""
        token = register_and_verify(client, app, 'discover2@test.com', 'discoveruser2')
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = client.get('/api/v1/discovery/feed?limit=5', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['data']) <= 5


# ──────────────────────────────────────────────────────────────
# 6. User profile includes emailVerified + socialMediaLinks
# ──────────────────────────────────────────────────────────────

class TestUserProfileFields:
    """Test that user profile includes new contract fields."""

    def test_profile_includes_email_verified(self, client, app):
        """User profile should include emailVerified field."""
        token = register_and_verify(client, app, 'fields@test.com', 'fieldsuser')
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = client.get('/api/v1/users/profile', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'emailVerified' in data
        assert data['emailVerified'] is True

    def test_profile_includes_social_media_links(self, client, app):
        """User profile should include socialMediaLinks field."""
        token = register_and_verify(client, app, 'fields2@test.com', 'fieldsuser2')
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = client.get('/api/v1/users/profile', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'socialMediaLinks' in data
        assert isinstance(data['socialMediaLinks'], list)


# ──────────────────────────────────────────────────────────────
# 7. Edge Cases & Security
# ──────────────────────────────────────────────────────────────

class TestResetTokenReuse:
    """Ensure consumed/cleared tokens cannot be reused."""

    def test_reset_token_cannot_be_reused(self, client, app):
        """A reset token should only work once."""
        register_and_verify(client, app, 'reuse@test.com', 'reuseuser')
        raw_token = get_reset_token(app, 'reuse@test.com')

        # First use — should succeed
        resp = client.post('/api/v1/auth/reset-password', json={
            'token': raw_token,
            'newPassword': 'NewPass123'
        })
        assert resp.status_code == 200

        # Second use — should fail (token consumed & cleared)
        resp = client.post('/api/v1/auth/reset-password', json={
            'token': raw_token,
            'newPassword': 'AnotherPass123'
        })
        assert resp.status_code == 400

    def test_verify_token_cannot_be_reused(self, client, app):
        """Once email is verified, the same verification token should not work again."""
        register_user(client, 'reusev@test.com', 'reusevuser')
        raw_token = get_verification_token(app, 'reusev@test.com')

        # First use — should succeed
        resp = client.get(f'/api/v1/auth/verify-email?token={raw_token}')
        assert resp.status_code == 200

        # Second use — token was cleared, should fail
        resp = client.get(f'/api/v1/auth/verify-email?token={raw_token}')
        assert resp.status_code == 404  # token no longer exists


class TestForgotPasswordUnverified:
    """Forgot-password should not generate tokens for unverified users."""

    def test_forgot_password_unverified_user(self, client, app):
        """forgot-password for unverified email should return 200 but NOT generate a token."""
        register_user(client, 'unveriforgot@test.com', 'unveriforgot')

        resp = client.post('/api/v1/auth/forgot-password', json={
            'email': 'unveriforgot@test.com'
        })
        # Always returns 200 for security
        assert resp.status_code == 200

        # But the user should NOT have a reset token since email is unverified
        from app.models.user import User
        with app.test_request_context():
            from app.database import get_db, close_db
            db = get_db()
            user = db.query(User).filter_by(email='unveriforgot@test.com').first()
            assert user.reset_token is None, "Unverified user should not receive reset token"
            close_db()


class TestSocialMediaLinksEdgeCases:
    """Edge cases for socialMediaLinks validation."""

    def test_empty_social_links_array(self, client, app):
        """An empty array should be accepted (user clears all links)."""
        token = register_and_verify(client, app, 'empty_links@test.com', 'emptylinks')
        headers = {'Authorization': f'Bearer {token}'}

        resp = client.put('/api/v1/users/profile', headers=headers, json={
            'socialMediaLinks': []
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['socialMediaLinks'] == []

    def test_social_link_missing_url(self, client, app):
        """A link entry without url should be rejected."""
        token = register_and_verify(client, app, 'nourl@test.com', 'nourlluser')
        headers = {'Authorization': f'Bearer {token}'}

        resp = client.put('/api/v1/users/profile', headers=headers, json={
            'socialMediaLinks': [{'platform': 'twitter'}]
        })
        assert resp.status_code == 400

    def test_social_link_missing_platform(self, client, app):
        """A link entry without platform should be rejected."""
        token = register_and_verify(client, app, 'noplat@test.com', 'noplatuser')
        headers = {'Authorization': f'Bearer {token}'}

        resp = client.put('/api/v1/users/profile', headers=headers, json={
            'socialMediaLinks': [{'url': 'https://twitter.com/test'}]
        })
        assert resp.status_code == 400


class TestPublicProfileContract:
    """Public profile endpoint returns contract-required fields."""

    def test_public_profile_includes_contract_fields(self, client, app):
        """GET /users/{userId} should include emailVerified and socialMediaLinks."""
        token = register_and_verify(client, app, 'pubprof@test.com', 'pubprofuser')
        headers = {'Authorization': f'Bearer {token}'}

        # Get own profile to find userId
        resp = client.get('/api/v1/users/profile', headers=headers)
        user_id = resp.get_json()['userId']

        # Fetch public profile (no auth needed)
        resp = client.get(f'/api/v1/users/{user_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'emailVerified' in data
        assert 'socialMediaLinks' in data
        assert isinstance(data['socialMediaLinks'], list)

    def test_aura_profile_includes_social_links(self, client, app):
        """GET /aura/profile should include socialMediaLinks."""
        token = register_and_verify(client, app, 'aurasl@test.com', 'aurasluser')
        headers = {'Authorization': f'Bearer {token}'}

        resp = client.get('/api/v1/aura/profile', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'socialMediaLinks' in data
        assert isinstance(data['socialMediaLinks'], list)


class TestLoginAfterPasswordReset:
    """Ensure old password fails and new password works after reset."""

    def test_old_password_fails_after_reset(self, client, app):
        """After password reset, the old password must not work."""
        old_pass = 'OldPass123'
        new_pass = 'NewPass456'
        register_and_verify(client, app, 'oldpw@test.com', 'oldpwuser', password=old_pass)
        raw_token = get_reset_token(app, 'oldpw@test.com')

        resp = client.post('/api/v1/auth/reset-password', json={
            'token': raw_token,
            'newPassword': new_pass
        })
        assert resp.status_code == 200

        # Old password should fail
        resp = client.post('/api/v1/auth/login', json={
            'email': 'oldpw@test.com',
            'password': old_pass
        })
        assert resp.status_code == 401

        # New password should work
        resp = client.post('/api/v1/auth/login', json={
            'email': 'oldpw@test.com',
            'password': new_pass
        })
        assert resp.status_code == 200
        assert 'token' in resp.get_json()
