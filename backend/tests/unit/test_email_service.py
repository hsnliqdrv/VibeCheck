"""
Tests for the Resend email integration:
  - email_service module (send_verification_email, send_password_reset_email)
  - Auth routes wired to send real emails on register / forgot-password

Uses Flask test client with SQLite (no running server or Docker needed).
All Resend API calls are mocked via unittest.mock.

Usage (from backend directory):
    pytest tests/unit/test_email_service.py -v

Optional explicit backend path (otherwise current directory is used):
    BACKEND_PATH=/absolute/path/to/backend pytest tests/unit/test_email_service.py -v
"""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

backend_root = Path(os.getenv("BACKEND_PATH", Path.cwd())).resolve()
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.config import Config
Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///test_email_vibecheck.db'

os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key')
os.environ['RESEND_API_KEY'] = 're_test_fake_key'
os.environ['EMAIL_FROM_ADDRESS'] = 'noreply@vibeaura.app'
os.environ['FRONTEND_URL'] = 'http://localhost:5173'

from app import create_app
from _helpers import register_user, get_verification_token, register_and_verify


# Note: app and client fixtures are provided by conftest.py


# Note: Helper functions are provided by _helpers.py


# ══════════════════════════════════════════════════════════════
# 1. Email service — direct function tests
# ══════════════════════════════════════════════════════════════

class TestSendVerificationEmail:
    """Test send_verification_email() in isolation."""

    @patch('app.services.email_service.resend.Emails.send')
    def test_calls_resend_api(self, mock_send, app):
        """Should call resend.Emails.send exactly once."""
        mock_send.return_value = {'id': 'mock-email-id'}
        from app.services.email_service import send_verification_email

        with app.test_request_context():
            send_verification_email('alice@example.com', 'alice', 'tok123')

        mock_send.assert_called_once()

    @patch('app.services.email_service.resend.Emails.send')
    def test_sends_to_correct_recipient(self, mock_send, app):
        """The 'to' field should contain only the target email."""
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_verification_email

        with app.test_request_context():
            send_verification_email('bob@example.com', 'bob', 'tok456')

        params = mock_send.call_args[0][0]
        assert params['to'] == ['bob@example.com']

    @patch('app.services.email_service.resend.Emails.send')
    def test_from_address_matches_config(self, mock_send, app):
        """The 'from' field should use EMAIL_FROM_ADDRESS from config."""
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_verification_email

        with app.test_request_context():
            send_verification_email('c@test.com', 'charlie', 'tok')

        params = mock_send.call_args[0][0]
        assert 'noreply@vibeaura.app' in params['from']
        assert 'VibeCheck' in params['from']

    @patch('app.services.email_service.resend.Emails.send')
    def test_subject_is_verification(self, mock_send, app):
        """Subject line should indicate account verification."""
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_verification_email

        with app.test_request_context():
            send_verification_email('d@test.com', 'diana', 'tok')

        params = mock_send.call_args[0][0]
        assert 'verify' in params['subject'].lower() or 'verification' in params['subject'].lower()

    @patch('app.services.email_service.resend.Emails.send')
    def test_html_contains_verification_url(self, mock_send, app):
        """Email body should contain a link to the frontend verify-email page."""
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_verification_email

        with app.test_request_context():
            send_verification_email('e@test.com', 'eve', 'my-secret-token')

        params = mock_send.call_args[0][0]
        html = params['html']
        assert 'http://localhost:5173/verify-email?token=my-secret-token' in html

    @patch('app.services.email_service.resend.Emails.send')
    def test_html_contains_username(self, mock_send, app):
        """Email body should greet the user by their username."""
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_verification_email

        with app.test_request_context():
            send_verification_email('f@test.com', 'frankie', 'tok')

        params = mock_send.call_args[0][0]
        assert 'frankie' in params['html']

    @patch('app.services.email_service.resend.Emails.send')
    def test_returns_resend_response(self, mock_send, app):
        """Should return the dict from Resend (contains the email id)."""
        mock_send.return_value = {'id': 'abc-123'}
        from app.services.email_service import send_verification_email

        with app.test_request_context():
            result = send_verification_email('g@test.com', 'grace', 'tok')

        assert result == {'id': 'abc-123'}


class TestSendPasswordResetEmail:
    """Test send_password_reset_email() in isolation."""

    @patch('app.services.email_service.resend.Emails.send')
    def test_calls_resend_api(self, mock_send, app):
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_password_reset_email

        with app.test_request_context():
            send_password_reset_email('alice@example.com', 'alice', 'reset-tok')

        mock_send.assert_called_once()

    @patch('app.services.email_service.resend.Emails.send')
    def test_sends_to_correct_recipient(self, mock_send, app):
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_password_reset_email

        with app.test_request_context():
            send_password_reset_email('bob@example.com', 'bob', 'reset-tok')

        params = mock_send.call_args[0][0]
        assert params['to'] == ['bob@example.com']

    @patch('app.services.email_service.resend.Emails.send')
    def test_subject_is_password_reset(self, mock_send, app):
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_password_reset_email

        with app.test_request_context():
            send_password_reset_email('c@test.com', 'charlie', 'reset-tok')

        params = mock_send.call_args[0][0]
        assert 'reset' in params['subject'].lower()

    @patch('app.services.email_service.resend.Emails.send')
    def test_html_contains_reset_url(self, mock_send, app):
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_password_reset_email

        with app.test_request_context():
            send_password_reset_email('d@test.com', 'diana', 'my-reset-token')

        params = mock_send.call_args[0][0]
        assert 'http://localhost:5173/reset-password?token=my-reset-token' in params['html']

    @patch('app.services.email_service.resend.Emails.send')
    def test_html_contains_username(self, mock_send, app):
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_password_reset_email

        with app.test_request_context():
            send_password_reset_email('e@test.com', 'frankie', 'reset-tok')

        params = mock_send.call_args[0][0]
        assert 'frankie' in params['html']

    @patch('app.services.email_service.resend.Emails.send')
    def test_from_address_matches_config(self, mock_send, app):
        mock_send.return_value = {'id': 'mock-id'}
        from app.services.email_service import send_password_reset_email

        with app.test_request_context():
            send_password_reset_email('f@test.com', 'grace', 'reset-tok')

        params = mock_send.call_args[0][0]
        assert 'noreply@vibeaura.app' in params['from']


class TestGetResendClient:
    """Test _get_resend_client error handling."""

    def test_raises_without_api_key(self, app):
        """Should raise RuntimeError when RESEND_API_KEY is not set."""
        from app.services.email_service import _get_resend_client

        app.config['RESEND_API_KEY'] = None
        with app.test_request_context():
            with pytest.raises(RuntimeError, match='RESEND_API_KEY'):
                _get_resend_client()
        app.config['RESEND_API_KEY'] = 're_test_fake_key'

    def test_raises_with_empty_string_key(self, app):
        """Empty string should also be treated as missing."""
        from app.services.email_service import _get_resend_client

        app.config['RESEND_API_KEY'] = ''
        with app.test_request_context():
            with pytest.raises(RuntimeError, match='RESEND_API_KEY'):
                _get_resend_client()
        app.config['RESEND_API_KEY'] = 're_test_fake_key'


class TestEmailHtmlTemplates:
    """Verify HTML template structure and content."""

    def test_verification_html_has_cta_button(self):
        from app.services.email_service import _verification_html
        html = _verification_html('testuser', 'https://example.com/verify?token=abc')
        assert 'Verify My Email' in html
        assert 'https://example.com/verify?token=abc' in html

    def test_verification_html_has_expiry_notice(self):
        from app.services.email_service import _verification_html
        html = _verification_html('testuser', 'https://example.com/verify?token=abc')
        assert '24 hours' in html

    def test_reset_html_has_cta_button(self):
        from app.services.email_service import _reset_password_html
        html = _reset_password_html('testuser', 'https://example.com/reset?token=xyz')
        assert 'Reset Password' in html
        assert 'https://example.com/reset?token=xyz' in html

    def test_reset_html_has_expiry_notice(self):
        from app.services.email_service import _reset_password_html
        html = _reset_password_html('testuser', 'https://example.com/reset?token=xyz')
        assert '1 hour' in html

    def test_verification_html_is_valid_html(self):
        from app.services.email_service import _verification_html
        html = _verification_html('user', 'https://example.com')
        assert '<!DOCTYPE html>' in html
        assert '</html>' in html
        assert '</body>' in html

    def test_reset_html_is_valid_html(self):
        from app.services.email_service import _reset_password_html
        html = _reset_password_html('user', 'https://example.com')
        assert '<!DOCTYPE html>' in html
        assert '</html>' in html
        assert '</body>' in html

    def test_verification_html_escapes_special_chars_in_url(self):
        from app.services.email_service import _verification_html
        html = _verification_html('user', 'https://example.com/verify?token=a&b=c')
        assert 'token=a&b=c' in html

    def test_reset_html_escapes_special_chars_in_url(self):
        from app.services.email_service import _reset_password_html
        html = _reset_password_html('user', 'https://example.com/reset?token=a&b=c')
        assert 'token=a&b=c' in html


# ══════════════════════════════════════════════════════════════
# 2. Registration route — email integration
# ══════════════════════════════════════════════════════════════

class TestRegistrationSendsEmail:
    """Verify that POST /auth/register triggers a verification email."""

    @patch('app.routes.auth.send_verification_email')
    def test_register_calls_send_verification_email(self, mock_send, client):
        """Registration should call send_verification_email."""
        mock_send.return_value = {'id': 'mock-id'}
        resp = register_user(client, 'email_r1@test.com', 'emailr1')
        assert resp.status_code == 201
        mock_send.assert_called_once()

    @patch('app.routes.auth.send_verification_email')
    def test_register_passes_correct_email(self, mock_send, client):
        """The email arg passed to send_verification_email should match the registrant."""
        mock_send.return_value = {'id': 'mock-id'}
        register_user(client, 'email_r2@test.com', 'emailr2')
        args = mock_send.call_args[0]
        assert args[0] == 'email_r2@test.com'

    @patch('app.routes.auth.send_verification_email')
    def test_register_passes_correct_username(self, mock_send, client):
        """The username arg should match what the user provided."""
        mock_send.return_value = {'id': 'mock-id'}
        register_user(client, 'email_r3@test.com', 'emailr3')
        args = mock_send.call_args[0]
        assert args[1] == 'emailr3'

    @patch('app.routes.auth.send_verification_email')
    def test_register_passes_a_token(self, mock_send, client):
        """A non-empty token string should be passed as the third arg."""
        mock_send.return_value = {'id': 'mock-id'}
        register_user(client, 'email_r4@test.com', 'emailr4')
        args = mock_send.call_args[0]
        token = args[2]
        assert isinstance(token, str)
        assert len(token) > 10

    @patch('app.routes.auth.send_verification_email')
    def test_register_succeeds_when_email_fails(self, mock_send, client):
        """If Resend is down, registration should still succeed (201)."""
        mock_send.side_effect = Exception('Resend API unreachable')
        resp = register_user(client, 'email_r5@test.com', 'emailr5')
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['emailVerificationRequired'] is True

    @patch('app.routes.auth.send_verification_email')
    def test_register_user_created_despite_email_failure(self, mock_send, client, app):
        """User should exist in DB even if email delivery failed."""
        mock_send.side_effect = Exception('Network error')
        resp = register_user(client, 'email_r6@test.com', 'emailr6')
        assert resp.status_code == 201

        from app.models.user import User
        with app.test_request_context():
            from app.database import get_db, close_db
            db = get_db()
            user = db.query(User).filter_by(email='email_r6@test.com').first()
            assert user is not None
            assert user.email_verified is False
            close_db()

    @patch('app.routes.auth.send_verification_email')
    def test_register_response_shape_unchanged(self, mock_send, client):
        """Response body shape should not change based on email success/failure."""
        mock_send.return_value = {'id': 'mock-id'}
        resp = register_user(client, 'email_r7@test.com', 'emailr7')
        data = resp.get_json()
        assert 'message' in data
        assert 'user' in data
        assert 'emailVerificationRequired' in data
        assert 'token' not in data


# ══════════════════════════════════════════════════════════════
# 3. Forgot-password route — email integration
# ══════════════════════════════════════════════════════════════

class TestForgotPasswordSendsEmail:
    """Verify that POST /auth/forgot-password triggers a reset email."""

    @patch('app.routes.auth.send_password_reset_email')
    def test_forgot_password_calls_send_email(self, mock_send, client, app):
        """Should call send_password_reset_email for verified users."""
        mock_send.return_value = {'id': 'mock-id'}
        register_and_verify(client, app, 'fp1@test.com', 'fpuser1')

        resp = client.post('/api/v1/auth/forgot-password', json={
            'email': 'fp1@test.com'
        })
        assert resp.status_code == 200
        mock_send.assert_called_once()

    @patch('app.routes.auth.send_password_reset_email')
    def test_forgot_password_passes_correct_email(self, mock_send, client, app):
        mock_send.return_value = {'id': 'mock-id'}
        register_and_verify(client, app, 'fp2@test.com', 'fpuser2')

        client.post('/api/v1/auth/forgot-password', json={
            'email': 'fp2@test.com'
        })
        args = mock_send.call_args[0]
        assert args[0] == 'fp2@test.com'

    @patch('app.routes.auth.send_password_reset_email')
    def test_forgot_password_passes_username(self, mock_send, client, app):
        mock_send.return_value = {'id': 'mock-id'}
        register_and_verify(client, app, 'fp3@test.com', 'fpuser3')

        client.post('/api/v1/auth/forgot-password', json={
            'email': 'fp3@test.com'
        })
        args = mock_send.call_args[0]
        assert args[1] == 'fpuser3'

    @patch('app.routes.auth.send_password_reset_email')
    def test_forgot_password_passes_token(self, mock_send, client, app):
        mock_send.return_value = {'id': 'mock-id'}
        register_and_verify(client, app, 'fp4@test.com', 'fpuser4')

        client.post('/api/v1/auth/forgot-password', json={
            'email': 'fp4@test.com'
        })
        args = mock_send.call_args[0]
        token = args[2]
        assert isinstance(token, str)
        assert len(token) > 10

    @patch('app.routes.auth.send_password_reset_email')
    def test_forgot_password_succeeds_when_email_fails(self, mock_send, client, app):
        """If Resend is down, forgot-password should still return 200."""
        mock_send.side_effect = Exception('Resend timeout')
        register_and_verify(client, app, 'fp5@test.com', 'fpuser5')

        resp = client.post('/api/v1/auth/forgot-password', json={
            'email': 'fp5@test.com'
        })
        assert resp.status_code == 200

    @patch('app.routes.auth.send_password_reset_email')
    def test_no_email_for_nonexistent_user(self, mock_send, client):
        """Should not call send_password_reset_email for unknown emails."""
        mock_send.return_value = {'id': 'mock-id'}
        resp = client.post('/api/v1/auth/forgot-password', json={
            'email': 'nobody_here@test.com'
        })
        assert resp.status_code == 200
        mock_send.assert_not_called()

    @patch('app.routes.auth.send_password_reset_email')
    def test_no_email_for_unverified_user(self, mock_send, client):
        """Unverified users should not receive a reset email."""
        mock_send.return_value = {'id': 'mock-id'}
        register_user(client, 'unverified_fp@test.com', 'unverfp')

        resp = client.post('/api/v1/auth/forgot-password', json={
            'email': 'unverified_fp@test.com'
        })
        assert resp.status_code == 200
        mock_send.assert_not_called()

    @patch('app.routes.auth.send_password_reset_email')
    def test_forgot_password_response_is_generic(self, mock_send, client, app):
        """Response message should be the same whether user exists or not (security)."""
        mock_send.return_value = {'id': 'mock-id'}
        register_and_verify(client, app, 'fp6@test.com', 'fpuser6')

        resp_exists = client.post('/api/v1/auth/forgot-password', json={
            'email': 'fp6@test.com'
        })
        resp_missing = client.post('/api/v1/auth/forgot-password', json={
            'email': 'doesnotexist_fp@test.com'
        })
        assert resp_exists.get_json()['message'] == resp_missing.get_json()['message']


# ══════════════════════════════════════════════════════════════
# 4. Config loading
# ══════════════════════════════════════════════════════════════

class TestEmailConfig:
    """Verify email-related config is loaded into Flask app."""

    def test_resend_api_key_in_config(self, app):
        assert app.config.get('RESEND_API_KEY') is not None

    def test_email_from_address_in_config(self, app):
        assert app.config.get('EMAIL_FROM_ADDRESS') == 'noreply@vibeaura.app'

    def test_frontend_url_in_config(self, app):
        assert app.config.get('FRONTEND_URL') == 'http://localhost:5173'

    def test_frontend_url_has_no_trailing_slash(self, app):
        url = app.config.get('FRONTEND_URL', '')
        assert not url.endswith('/')
