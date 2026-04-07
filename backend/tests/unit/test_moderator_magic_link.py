from unittest.mock import patch

from tests.unit._helpers import register_user


class TestModeratorMagicLink:
    def test_login_returns_generic_error_and_sends_magic_link_for_moderator(self, client, app):
        register_user(client, 'mod1@test.com', 'moduser1')

        with app.test_request_context():
            from app.database import get_db, close_db
            from app.models.user import User

            db = get_db()
            user = db.query(User).filter_by(email='mod1@test.com').first()
            assert user is not None
            setattr(user, 'role', 'moderator')
            setattr(user, 'email_verified', True)
            db.commit()
            close_db()

        with patch('app.routes.auth.send_moderator_magic_link_email') as mock_send:
            mock_send.return_value = {'id': 'mock-id'}

            login_resp = client.post('/api/v1/auth/login', json={
                'email': 'mod1@test.com',
                'password': 'Test1234',
            })

            assert login_resp.status_code == 401
            data = login_resp.get_json()
            assert data['message'] == 'Invalid email or password'
            mock_send.assert_called_once()

            sent_email, sent_username, raw_magic_token = mock_send.call_args[0]
            assert sent_email == 'mod1@test.com'
            assert sent_username == 'moduser1'
            assert isinstance(raw_magic_token, str)
            assert len(raw_magic_token) > 10

            exchange_resp = client.get(f'/api/v1/auth/moderator-login/{raw_magic_token}')
            assert exchange_resp.status_code == 200
            exchange_data = exchange_resp.get_json()
            assert 'token' in exchange_data
            assert exchange_data['user']['role'] == 'moderator'

            reuse_resp = client.get(f'/api/v1/auth/moderator-login/{raw_magic_token}')
            assert reuse_resp.status_code == 401
