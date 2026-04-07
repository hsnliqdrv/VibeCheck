from tests.unit._helpers import get_first_room_id, register_and_verify


class TestRoomPostReporting:
    """Test reporting a post inside a room."""

    def test_report_room_post_persists_report(self, client, app):
        """POST /social/rooms/{roomId}/posts/{postId}/report should store reporter, owner, room, and reason."""
        room_id = get_first_room_id(app)
        assert room_id is not None

        author_token = register_and_verify(client, app, 'report-author@test.com', 'reportauthor')
        reporter_token = register_and_verify(client, app, 'report-reporter@test.com', 'reportreporter')

        author_headers = {'Authorization': f'Bearer {author_token}'}
        reporter_headers = {'Authorization': f'Bearer {reporter_token}'}

        create_response = client.post(f'/api/v1/social/rooms/{room_id}/posts', headers=author_headers, json={
            'category': 'cinema',
            'title': 'Reportable room post',
            'image': 'https://example.com/reportable-post.jpg',
        })
        assert create_response.status_code == 201
        post_data = create_response.get_json()['post']
        post_id = post_data['id']

        report_response = client.post(
            f'/api/v1/social/rooms/{room_id}/posts/{post_id}/report',
            headers=reporter_headers,
            json={'reason': 'Spam or self-promotion'},
        )
        assert report_response.status_code == 201

        payload = report_response.get_json()
        assert payload['message'] == 'Report submitted successfully'
        report = payload['report']
        assert report['roomId'] == room_id
        assert report['postId'] == post_id
        assert report['reason'] == 'Spam or self-promotion'

        from app.models.report import RoomPostReport
        from app.models.post import Post
        from app.models.user import User

        with app.test_request_context():
            from app.database import get_db, close_db

            db = get_db()

            stored_report = db.query(RoomPostReport).filter_by(post_id=post_id).first()
            if stored_report is None:
                raise AssertionError('Expected report to be persisted')
            report_data = stored_report.to_dict()
            assert report_data['roomId'] == room_id
            assert report_data['reason'] == 'Spam or self-promotion'

            reported_post = db.query(Post).filter_by(id=post_id).first()
            if reported_post is None:
                raise AssertionError('Expected reported post to exist')
            assert report_data['ownerId'] == reported_post.user_id

            reporter_user = db.query(User).filter_by(email='report-reporter@test.com').first()
            if reporter_user is None:
                raise AssertionError('Expected reporter user to exist')
            assert report_data['reporterId'] == reporter_user.user_id
            close_db()
