from flask_jwt_extended import create_access_token

from tests.unit._helpers import get_first_room_id, register_and_verify


class TestModerationEndpoints:
    def test_moderator_can_list_reports_suspend_user_and_delete_room_post(self, client, app):
        mod_token = register_and_verify(client, app, 'modflow@test.com', 'modflow')
        owner_token = register_and_verify(client, app, 'ownerflow@test.com', 'ownerflow')
        reporter_token = register_and_verify(client, app, 'reporterflow@test.com', 'reporterflow')

        assert mod_token is not None
        assert owner_token is not None
        assert reporter_token is not None

        room_id = get_first_room_id(app)
        assert room_id is not None

        with app.test_request_context():
            from app.database import get_db, close_db
            from app.models.user import User

            db = get_db()
            mod_user = db.query(User).filter_by(email='modflow@test.com').first()
            assert mod_user is not None
            setattr(mod_user, 'role', 'moderator')
            db.commit()

            moderator_access_token = create_access_token(identity=mod_user.user_id)
            close_db()

        owner_headers = {'Authorization': f'Bearer {owner_token}'}
        reporter_headers = {'Authorization': f'Bearer {reporter_token}'}
        moderator_headers = {'Authorization': f'Bearer {moderator_access_token}'}

        create_post_resp = client.post(
            f'/api/v1/social/rooms/{room_id}/posts',
            headers=owner_headers,
            json={
                'category': 'cinema',
                'title': 'Report target post',
                'image': 'https://example.com/post.png',
            },
        )
        assert create_post_resp.status_code == 201
        post_id = create_post_resp.get_json()['post']['id']

        report_resp = client.post(
            f'/api/v1/social/rooms/{room_id}/posts/{post_id}/report',
            headers=reporter_headers,
            json={'reason': 'Offensive content'},
        )
        assert report_resp.status_code == 201

        reports_resp = client.get('/api/v1/moderation/reports', headers=moderator_headers)
        assert reports_resp.status_code == 200
        reports_data = reports_resp.get_json()
        assert reports_data['total'] >= 1
        first_item = reports_data['data'][0]
        assert first_item['report']['postId'] == post_id
        assert first_item['report']['reason'] == 'Offensive content'

        owner_user_id = first_item['owner']['userId']
        suspend_resp = client.post(
            f'/api/v1/moderation/users/{owner_user_id}/suspend',
            headers=moderator_headers,
            json={'durationHours': 24, 'reason': 'Repeated violations'},
        )
        assert suspend_resp.status_code == 200
        suspended_user = suspend_resp.get_json()['user']
        assert suspended_user['suspendedUntil'] is not None
        assert suspended_user['suspensionReason'] == 'Repeated violations'

        blocked_post_resp = client.post(
            f'/api/v1/social/rooms/{room_id}/posts',
            headers=owner_headers,
            json={
                'category': 'cinema',
                'title': 'Blocked by suspension',
                'image': 'https://example.com/blocked.png',
            },
        )
        assert blocked_post_resp.status_code == 403

        delete_resp = client.delete(
            f'/api/v1/moderation/room-posts/{post_id}',
            headers=moderator_headers,
        )
        assert delete_resp.status_code == 204
