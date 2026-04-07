from tests.unit._helpers import register_and_verify


class TestSocialMediaLinks:
    """Test socialMediaLinks validation on PUT /users/profile."""

    def test_social_links_flow(self, client, app):
        """Test the full social links flow: update, get profile, get public profile."""
        token = register_and_verify(client, app, 'social@test.com', 'socialuser')
        headers = {'Authorization': f'Bearer {token}'}

        resp = client.put('/api/v1/users/profile', headers=headers, json={
            'socialMediaLinks': [
                {'platform': 'instagram', 'url': 'https://instagram.com/testuser'},
                {'platform': 'twitter', 'url': 'https://twitter.com/testuser'},
            ]
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['socialMediaLinks']) == 2

        resp = client.get('/api/v1/users/profile', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'socialMediaLinks' in data
        user_id = data['userId']

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

        resp = client.get('/api/v1/users/profile', headers=headers)
        user_id = resp.get_json()['userId']

        resp = client.get(f'/api/v1/users/{user_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'emailVerified' in data
        assert 'socialMediaLinks' in data
        assert isinstance(data['socialMediaLinks'], list)
