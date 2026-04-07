from tests.unit._helpers import get_verification_token, register_and_verify, register_user


class TestEmailVerification:
    """Test the full registration -> verification -> login flow."""

    def test_register_returns_no_token(self, client):
        """Registration should NOT issue a JWT and should require email verification."""
        resp = register_user(client, 'verify@test.com', 'verifyuser')
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'token' not in data, 'Registration should not issue JWT'
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
        assert 'token' in data, 'Verify-email should return a JWT'
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
