from tests.unit._helpers import register_and_verify


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
