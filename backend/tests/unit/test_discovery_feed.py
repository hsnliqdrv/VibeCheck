from tests.unit._helpers import register_and_verify


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
