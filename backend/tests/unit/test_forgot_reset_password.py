from tests.unit._helpers import get_reset_token, register_and_verify, register_user, get_verification_token


class TestForgotResetPassword:
    """Test the forgot-password -> reset-password flow."""

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


class TestForgotPasswordUnverified:
    """Forgot-password should not generate tokens for unverified users."""

    def test_forgot_password_unverified_user(self, client, app):
        """forgot-password for unverified email should return 200 but NOT generate a token."""
        register_user(client, 'unveriforgot@test.com', 'unveriforgot')

        resp = client.post('/api/v1/auth/forgot-password', json={
            'email': 'unveriforgot@test.com'
        })
        assert resp.status_code == 200

        from app.models.user import User
        with app.test_request_context():
            from app.database import get_db, close_db

            db = get_db()
            user = db.query(User).filter_by(email='unveriforgot@test.com').first()
            assert user is not None
            assert user.reset_token is None, 'Unverified user should not receive reset token'
            close_db()


class TestResetTokenReuse:
    """Ensure consumed/cleared tokens cannot be reused."""

    def test_reset_token_cannot_be_reused(self, client, app):
        """A reset token should only work once."""
        register_and_verify(client, app, 'reuse@test.com', 'reuseuser')
        raw_token = get_reset_token(app, 'reuse@test.com')

        resp = client.post('/api/v1/auth/reset-password', json={
            'token': raw_token,
            'newPassword': 'NewPass123'
        })
        assert resp.status_code == 200

        resp = client.post('/api/v1/auth/reset-password', json={
            'token': raw_token,
            'newPassword': 'AnotherPass123'
        })
        assert resp.status_code == 400

    def test_verify_token_cannot_be_reused(self, client, app):
        """Once email is verified, the same verification token should not work again."""
        register_user(client, 'reusev@test.com', 'reusevuser')
        raw_token = get_verification_token(app, 'reusev@test.com')

        resp = client.get(f'/api/v1/auth/verify-email?token={raw_token}')
        assert resp.status_code == 200

        resp = client.get(f'/api/v1/auth/verify-email?token={raw_token}')
        assert resp.status_code == 404
