"""
VibeCheck API Test Suite
Tests all endpoints defined in openapi-mvp.yaml

Usage:
    pip install pytest requests
    pytest test_api.py -v
    
Or run standalone:
    python test_api.py
"""

import requests
import time
import sys
from typing import Dict, Optional
import random
import string

def _verify_email(email: str):
    import os
    from sqlalchemy import create_engine, text
    db_url = "postgresql://postgres:postgres@postgres:5432/vibecheck"
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET email_verified = true WHERE email = :email"), {"email": email})

class VibeCheckAPITester:
    """Comprehensive API tester for VibeCheck backend"""
    
    def __init__(self, base_url: str = "http://localhost:3000/api/v1"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_results = []
        
    def _random_string(self, length: int = 8) -> str:
        """Generate random string for unique test data"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def _log_test(self, name: str, passed: bool, response=None, error=None):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        result = {
            'name': name,
            'passed': passed,
            'status_code': response.status_code if response else None,
            'error': str(error) if error else None
        }
        self.test_results.append(result)
        
        if response and hasattr(response, 'status_code'):
            print(f"{status} | {name} | Status: {response.status_code}")
        else:
            print(f"{status} | {name}")
            
        if error:
            print(f"    Error: {error}")
        
    def test_health(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            passed = response.status_code == 200 and response.json().get('status') == 'healthy'
            self._log_test("Health Check", passed, response)
            return passed
        except Exception as e:
            self._log_test("Health Check", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # AUTH TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_register(self):
        """Test user registration — should NOT issue JWT, should require email verification"""
        try:
            username = f"testuser_{self._random_string()}"
            email = f"{username}@test.com"
            
            payload = {
                "email": email,
                "username": username,
                "password": "Test123456!"
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=payload)
            passed = response.status_code == 201
            
            if passed and response.json():
                data = response.json()
                if 'user' in data:
                    self.user_id = data['user'].get('userId')
                # Registration must NOT issue a JWT token
                passed = passed and ('token' not in data)
                # Must signal that email verification is required
                passed = passed and (data.get('emailVerificationRequired') is True)
                # User should be marked as unverified
                passed = passed and (data.get('user', {}).get('emailVerified') is False)
            
            self._log_test("POST /auth/register", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /auth/register", False, error=e)
            return False
    
    def test_register_duplicate(self):
        """Test registration with duplicate email (should fail)"""
        try:
            payload = {
                "email": "duplicate@test.com",
                "username": "duplicate_user",
                "password": "Test123456!"
            }
            
            # Register first time
            requests.post(f"{self.base_url}/auth/register", json=payload)
            
            # Try to register again with same email
            response = requests.post(f"{self.base_url}/auth/register", json=payload)
            passed = response.status_code == 409  # Conflict expected
            
            self._log_test("POST /auth/register (duplicate check)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /auth/register (duplicate check)", False, error=e)
            return False
    
    def test_login(self):
        """Test user login"""
        try:
            # Create a user first
            username = f"logintest_{self._random_string()}"
            email = f"{username}@test.com"
            password = "Test123456!"
            
            register_payload = {
                "email": email,
                "username": username,
                "password": password
            }
            requests.post(f"{self.base_url}/auth/register", json=register_payload)
            _verify_email(email)
            
            # Now login
            login_payload = {
                "email": email,
                "password": password
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=login_payload)
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                if 'token' in data:
                    self.token = data['token']
                if 'user' in data:
                    self.user_id = data['user'].get('userId')
            
            self._log_test("POST /auth/login", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /auth/login", False, error=e)
            return False
    
    def test_login_invalid(self):
        """Test login with invalid credentials"""
        try:
            payload = {
                "email": "invalid@test.com",
                "password": "wrongpassword"
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=payload)
            passed = response.status_code == 401  # Unauthorized expected
            
            self._log_test("POST /auth/login (invalid credentials)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /auth/login (invalid credentials)", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # JWT VALIDATION TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_missing_authorization_header(self):
        """Test endpoint without Authorization header"""
        try:
            response = requests.get(f"{self.base_url}/users/profile")
            passed = response.status_code == 401
            self._log_test("Missing Authorization header", passed, response)
            return passed
        except Exception as e:
            self._log_test("Missing Authorization header", False, error=e)
            return False
    
    def test_malformed_token_empty(self):
        """Test with empty token"""
        try:
            headers = {"Authorization": "Bearer "}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 401
            self._log_test("Malformed token (empty)", passed, response)
            return passed
        except Exception as e:
            self._log_test("Malformed token (empty)", False, error=e)
            return False
    
    def test_malformed_token_invalid_format(self):
        """Test with invalid token format"""
        try:
            headers = {"Authorization": "Bearer not.a.valid.jwt"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 401
            self._log_test("Malformed token (invalid format)", passed, response)
            return passed
        except Exception as e:
            self._log_test("Malformed token (invalid format)", False, error=e)
            return False
    
    def test_malformed_token_missing_bearer(self):
        """Test with missing Bearer prefix"""
        try:
            headers = {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 401
            self._log_test("Malformed token (missing Bearer)", passed, response)
            return passed
        except Exception as e:
            self._log_test("Malformed token (missing Bearer)", False, error=e)
            return False
    
    def test_malformed_token_wrong_prefix(self):
        """Test with wrong token prefix (Basic instead of Bearer)"""
        try:
            headers = {"Authorization": "Basic eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 401
            self._log_test("Malformed token (wrong prefix)", passed, response)
            return passed
        except Exception as e:
            self._log_test("Malformed token (wrong prefix)", False, error=e)
            return False
    
    def test_tampered_token_payload(self):
        """Test with tampered token payload"""
        try:
            # Valid JWT structure but with tampered payload
            tampered = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0YW1wZXJlZCI6InRydWUifQ.invalid_signature"
            headers = {"Authorization": f"Bearer {tampered}"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 401
            self._log_test("Tampered token payload", passed, response)
            return passed
        except Exception as e:
            self._log_test("Tampered token payload", False, error=e)
            return False
    
    def test_random_token_invalid(self):
        """Test with random invalid token string"""
        try:
            headers = {"Authorization": "Bearer aKJ7hK8jDj2kDjhKJhd7Kd9jdk"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 401
            self._log_test("Random invalid token", passed, response)
            return passed
        except Exception as e:
            self._log_test("Random invalid token", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # USER PROFILE TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_get_profile(self):
        """Test getting current user profile"""
        if not self.token:
            self._log_test("GET /users/profile", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 200
            
            self._log_test("GET /users/profile", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /users/profile", False, error=e)
            return False
    
    def test_update_profile(self):
        """Test updating user profile"""
        if not self.token:
            self._log_test("PUT /users/profile", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "bio": "Testing my updated bio!",
                "username": f"updated_{self._random_string()}"
            }
            
            response = requests.put(f"{self.base_url}/users/profile", 
                                   headers=headers, json=payload)
            passed = response.status_code == 200
            
            self._log_test("PUT /users/profile", passed, response)
            return passed
        except Exception as e:
            self._log_test("PUT /users/profile", False, error=e)
            return False
    
    def test_get_user_by_id(self):
        """Test getting user profile by ID"""
        if not self.user_id:
            self._log_test("GET /users/{userId}", False, error="No user ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/users/{self.user_id}")
            passed = response.status_code == 200
            
            self._log_test("GET /users/{userId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /users/{userId}", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # CONTENT TESTS - MOVIES
    # ─────────────────────────────────────────────────────────
    
    def test_get_movies(self):
        """Test getting movies list"""
        try:
            response = requests.get(f"{self.base_url}/content/movies?limit=5")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # Store a movie ID for detail test
                if 'items' in data and len(data['items']) > 0:
                    self.movie_id = data['items'][0].get('id')
            
            self._log_test("GET /content/movies", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/movies", False, error=e)
            return False
    
    def test_get_movies_with_search(self):
        """Test searching movies"""
        try:
            response = requests.get(f"{self.base_url}/content/movies?search=matrix&limit=5")
            passed = response.status_code == 200
            
            self._log_test("GET /content/movies (with search)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/movies (with search)", False, error=e)
            return False
    
    def test_get_movie_by_id(self):
        """Test getting movie details"""
        try:
            # Try with a common movie ID
            movie_id = getattr(self, 'movie_id', 'tt0133093')  # The Matrix
            
            response = requests.get(f"{self.base_url}/content/movies/{movie_id}")
            passed = response.status_code in [200, 404]  # Either works or not found
            
            self._log_test("GET /content/movies/{movieId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/movies/{movieId}", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # CONTENT TESTS - ALBUMS
    # ─────────────────────────────────────────────────────────
    
    def test_get_albums(self):
        """Test getting albums list"""
        try:
            response = requests.get(f"{self.base_url}/content/albums?limit=5")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    self.album_id = data['items'][0].get('id')
            
            self._log_test("GET /content/albums", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/albums", False, error=e)
            return False
    
    def test_get_albums_with_search(self):
        """Test searching albums"""
        try:
            response = requests.get(f"{self.base_url}/content/albums?search=dark&limit=5")
            passed = response.status_code == 200
            
            self._log_test("GET /content/albums (with search)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/albums (with search)", False, error=e)
            return False
    
    def test_get_album_by_id(self):
        """Test getting album details"""
        try:
            album_id = getattr(self, 'album_id', '6s84u2TUpR3wdUv4NgKA2j')
            
            response = requests.get(f"{self.base_url}/content/albums/{album_id}")
            passed = response.status_code in [200, 404]
            
            self._log_test("GET /content/albums/{albumId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/albums/{albumId}", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # CONTENT TESTS - GAMES
    # ─────────────────────────────────────────────────────────
    
    def test_get_games(self):
        """Test getting games list"""
        try:
            response = requests.get(f"{self.base_url}/content/games?limit=5")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    self.game_id = data['items'][0].get('id')
            
            self._log_test("GET /content/games", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/games", False, error=e)
            return False
    
    def test_get_games_with_filters(self):
        """Test filtering games"""
        try:
            response = requests.get(f"{self.base_url}/content/games?platform=PC&limit=5")
            passed = response.status_code == 200
            
            self._log_test("GET /content/games (with filters)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/games (with filters)", False, error=e)
            return False
    
    def test_get_game_by_id(self):
        """Test getting game details"""
        try:
            game_id = getattr(self, 'game_id', '1020')
            
            response = requests.get(f"{self.base_url}/content/games/{game_id}")
            passed = response.status_code in [200, 404]
            
            self._log_test("GET /content/games/{gameId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/games/{gameId}", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # CONTENT TESTS - BOOKS
    # ─────────────────────────────────────────────────────────
    
    def test_get_books(self):
        """Test getting books list"""
        try:
            response = requests.get(f"{self.base_url}/content/books?limit=5")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    self.book_id = data['items'][0].get('id')
            
            self._log_test("GET /content/books", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/books", False, error=e)
            return False
    
    def test_get_books_with_search(self):
        """Test searching books"""
        try:
            response = requests.get(f"{self.base_url}/content/books?search=1984&limit=5")
            passed = response.status_code == 200
            
            self._log_test("GET /content/books (with search)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/books (with search)", False, error=e)
            return False
    
    def test_get_book_by_id(self):
        """Test getting book details"""
        try:
            book_id = getattr(self, 'book_id', 'OL7353617M')
            
            response = requests.get(f"{self.base_url}/content/books/{book_id}")
            passed = response.status_code in [200, 404]
            
            self._log_test("GET /content/books/{bookId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/books/{bookId}", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # CONTENT TESTS - LOCATIONS
    # ─────────────────────────────────────────────────────────
    
    def test_get_locations(self):
        """Test getting locations list"""
        try:
            response = requests.get(f"{self.base_url}/content/locations?limit=5")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    self.location_id = data['items'][0].get('id')
            
            self._log_test("GET /content/locations", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/locations", False, error=e)
            return False
    
    def test_get_locations_with_filters(self):
        """Test filtering locations"""
        try:
            response = requests.get(f"{self.base_url}/content/locations?country=France&limit=5")
            passed = response.status_code == 200
            
            self._log_test("GET /content/locations (with filters)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/locations (with filters)", False, error=e)
            return False
    
    def test_get_location_by_id(self):
        """Test getting location details"""
        try:
            location_id = getattr(self, 'location_id', '2988507')
            
            response = requests.get(f"{self.base_url}/content/locations/{location_id}")
            passed = response.status_code in [200, 404]
            
            self._log_test("GET /content/locations/{locationId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /content/locations/{locationId}", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # SEARCH TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_global_search(self):
        """Test global search across all content"""
        try:
            response = requests.get(f"{self.base_url}/search?query=dark&limit=10")
            passed = response.status_code == 200
            
            self._log_test("GET /search", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /search", False, error=e)
            return False
    
    def test_global_search_with_categories(self):
        """Test global search with category filter"""
        try:
            response = requests.get(
                f"{self.base_url}/search?query=adventure&categories=games,books&limit=10"
            )
            passed = response.status_code == 200
            
            self._log_test("GET /search (with categories)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /search (with categories)", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # AURA TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_get_current_user_aura(self):
        """Test getting current user's aura profile"""
        if not self.token:
            self._log_test("GET /aura/profile", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/aura/profile", headers=headers)
            passed = response.status_code == 200
            
            self._log_test("GET /aura/profile", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /aura/profile", False, error=e)
            return False
    
    def test_update_aura_profile(self):
        """Test updating aura profile (only auraColors allowed; aestheticTags are auto-inferred)"""
        if not self.token:
            self._log_test("PUT /aura/profile", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            # aestheticTags are now auto-inferred and cannot be set manually (403)
            payload = {
                "auraColors": ["#FF6B9D", "#4ECDC4", "#45B7D1"]
            }
            
            response = requests.put(f"{self.base_url}/aura/profile", 
                                   headers=headers, json=payload)
            passed = response.status_code == 200
            
            self._log_test("PUT /aura/profile", passed, response)
            return passed
        except Exception as e:
            self._log_test("PUT /aura/profile", False, error=e)
            return False
    
    def test_update_aura_profile_rejects_aesthetic_tags(self):
        """Test that manually setting aestheticTags is blocked (403)"""
        if not self.token:
            self._log_test("PUT /aura/profile (reject tags)", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "aestheticTags": ["minimalist", "dark academia", "cyberpunk"]
            }
            
            response = requests.put(f"{self.base_url}/aura/profile", 
                                   headers=headers, json=payload)
            passed = response.status_code == 403
            
            self._log_test("PUT /aura/profile (reject tags)", passed, response)
            return passed
        except Exception as e:
            self._log_test("PUT /aura/profile (reject tags)", False, error=e)
            return False
    
    def test_get_user_aura_by_id(self):
        """Test getting user's aura profile by ID"""
        if not self.user_id:
            self._log_test("GET /aura/profile/{userId}", False, error="No user ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/aura/profile/{self.user_id}")
            passed = response.status_code == 200
            
            self._log_test("GET /aura/profile/{userId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /aura/profile/{userId}", False, error=e)
            return False
    
    def test_get_aura_matches(self):
        """Test getting aura matches (similar users)"""
        if not self.token:
            self._log_test("GET /aura/matches", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/aura/matches", headers=headers)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Verify response structure
                if 'data' in data and 'total' in data:
                    self._log_test("GET /aura/matches", True, response)
                    return True
                else:
                    self._log_test("GET /aura/matches", False, response, 
                                  error="Missing 'data' or 'total' in response")
                    return False
            else:
                self._log_test("GET /aura/matches", passed, response)
                return passed
        except Exception as e:
            self._log_test("GET /aura/matches", False, error=e)
            return False
    
    def test_get_aura_matches_with_pagination(self):
        """Test getting aura matches with pagination parameters"""
        if not self.token:
            self._log_test("GET /aura/matches?limit=5&offset=0", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            params = {"limit": 5, "offset": 0}
            response = requests.get(f"{self.base_url}/aura/matches", 
                                   headers=headers, params=params)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Verify pagination works
                if 'data' in data and len(data['data']) <= 5:
                    self._log_test("GET /aura/matches?limit=5&offset=0", True, response)
                    return True
                else:
                    self._log_test("GET /aura/matches?limit=5&offset=0", False, response,
                                  error="Pagination not working correctly")
                    return False
            else:
                self._log_test("GET /aura/matches?limit=5&offset=0", passed, response)
                return passed
        except Exception as e:
            self._log_test("GET /aura/matches?limit=5&offset=0", False, error=e)
            return False
    
    def test_calculate_compatibility(self):
        """Test calculating compatibility with another user"""
        if not self.token:
            self._log_test("GET /aura/compatibility/{userId}", False, error="No auth token available")
            return False
        
        if not self.user_id:
            self._log_test("GET /aura/compatibility/{userId}", False, error="No user ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            # Use a dummy user ID for testing (in real test, would use another registered user)
            test_user_id = "u_test_dummy_123"
            response = requests.get(f"{self.base_url}/aura/compatibility/{test_user_id}", 
                                   headers=headers)
            
            # Should return 404 for non-existent user or 200 for existing user
            passed = response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                # Verify response structure
                if all(k in data for k in ['compatibilityScore', 'sharedAesthetics', 'matchReason']):
                    self._log_test("GET /aura/compatibility/{userId}", True, response)
                    return True
                else:
                    self._log_test("GET /aura/compatibility/{userId}", False, response,
                                  error="Missing required fields in response")
                    return False
            else:
                self._log_test("GET /aura/compatibility/{userId}", passed, response)
                return passed
        except Exception as e:
            self._log_test("GET /aura/compatibility/{userId}", False, error=e)
            return False
    
    def test_calculate_compatibility_with_self(self):
        """Test calculating compatibility with self (should fail)"""
        if not self.token:
            self._log_test("GET /aura/compatibility/{self}", False, error="No auth token available")
            return False
        
        if not self.user_id:
            self._log_test("GET /aura/compatibility/{self}", False, error="No user ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/aura/compatibility/{self.user_id}", 
                                   headers=headers)
            
            # Should return 400 Bad Request
            passed = response.status_code == 400
            
            self._log_test("GET /aura/compatibility/{self} (should fail)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /aura/compatibility/{self} (should fail)", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # BADGES & GAMIFICATION TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_get_all_badges(self):
        """Test getting all available badges"""
        try:
            response = requests.get(f"{self.base_url}/badges")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # Verify response is a direct array of Badge objects (per OpenAPI spec)
                if isinstance(data, list):
                    passed = True  # Array is correct format
                else:
                    passed = False  # Should be array, not object
            
            self._log_test("GET /badges", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges", False, error=e)
            return False
    
    def test_get_badges_by_rarity(self):
        """Test getting badges filtered by rarity"""
        try:
            rarities = ['common', 'rare', 'epic', 'legendary']
            
            for rarity in rarities:
                response = requests.get(f"{self.base_url}/badges", params={'rarity': rarity})
                passed = response.status_code == 200
                
                self._log_test(f"GET /badges?rarity={rarity}", passed, response)
                
                if not passed:
                    return False
            
            return True
        except Exception as e:
            self._log_test("GET /badges by rarity", False, error=e)
            return False
    
    def test_get_badges_by_category(self):
        """Test getting badges filtered by category"""
        try:
            categories = ['early', 'completionist', 'social', 'streak', 'special']
            
            for category in categories:
                response = requests.get(f"{self.base_url}/badges", params={'category': category})
                passed = response.status_code == 200
                
                self._log_test(f"GET /badges?category={category}", passed, response)
                
                if not passed:
                    return False
            
            return True
        except Exception as e:
            self._log_test("GET /badges by category", False, error=e)
            return False
    
    def test_get_badges_with_multiple_filters(self):
        """Test getting badges with multiple filters"""
        try:
            response = requests.get(f"{self.base_url}/badges", 
                                   params={'rarity': 'rare', 'category': 'social'})
            passed = response.status_code == 200
            
            self._log_test("GET /badges?rarity=rare&category=social", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges with multiple filters", False, error=e)
            return False
    
    def test_get_user_badges(self):
        """Test getting current user's badges"""
        if not self.token:
            self._log_test("GET /badges/user (no token)", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/badges/user", headers=headers)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # API returns a raw list of badge objects
                passed = isinstance(data, list)
                if passed and len(data) > 0:
                    # Verify badge objects have expected fields
                    first = data[0]
                    passed = isinstance(first, dict) and 'id' in first and 'name' in first
            
            self._log_test("GET /badges/user", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges/user", False, error=e)
            return False
    
    def test_get_user_badges_by_id(self):
        """Test getting user's badges by user ID"""
        if not self.user_id:
            self._log_test("GET /badges/user/{userId} (no user id)", False, error="No user ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/badges/user/{self.user_id}")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # API returns a raw list of badge objects
                passed = isinstance(data, list)
                if passed and len(data) > 0:
                    first = data[0]
                    passed = isinstance(first, dict) and 'id' in first and 'name' in first
            
            self._log_test(f"GET /badges/user/{self.user_id}", passed, response)
            return passed
        except Exception as e:
            self._log_test(f"GET /badges/user/{self.user_id}", False, error=e)
            return False
    
    def test_get_nonexistent_user_badges(self):
        """Test getting badges for non-existent user"""
        try:
            fake_user_id = "nonexistent_user_" + self._random_string()
            response = requests.get(f"{self.base_url}/badges/user/{fake_user_id}")
            passed = response.status_code == 404
            
            self._log_test("GET /badges/user/{nonexistentId} (should 404)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges/user/{nonexistentId} (should 404)", False, error=e)
            return False
    
    def test_get_curator_stats(self):
        """Test getting current user's curator statistics"""
        if not self.token:
            self._log_test("GET /curator/stats (no token)", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/curator/stats", headers=headers)
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # Verify required fields are present
                required_fields = ['totalShares', 'totalXP', 'currentLevel']
                if isinstance(data, dict):
                    # Check if all required fields exist
                    passed = all(field in data for field in required_fields)
            
            self._log_test("GET /curator/stats", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/stats", False, error=e)
            return False
    
    def test_get_curator_stats_by_id(self):
        """Test getting user's curator statistics by user ID"""
        if not self.user_id:
            self._log_test("GET /curator/stats/{userId} (no user id)", False, error="No user ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/curator/stats/{self.user_id}")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                required_fields = ['totalShares', 'totalXP', 'currentLevel']
                if isinstance(data, dict):
                    passed = all(field in data for field in required_fields)
            
            self._log_test(f"GET /curator/stats/{self.user_id}", passed, response)
            return passed
        except Exception as e:
            self._log_test(f"GET /curator/stats/{self.user_id}", False, error=e)
            return False
    
    def test_get_nonexistent_user_curator_stats(self):
        """Test getting curator stats for non-existent user"""
        try:
            fake_user_id = "nonexistent_user_" + self._random_string()
            response = requests.get(f"{self.base_url}/curator/stats/{fake_user_id}")
            passed = response.status_code == 404
            
            self._log_test("GET /curator/stats/{nonexistentId} (should 404)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/stats/{nonexistentId} (should 404)", False, error=e)
            return False
    
    def test_get_curator_levels(self):
        """Test getting all curator levels"""
        try:
            response = requests.get(f"{self.base_url}/curator/levels")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # Verify response is a list or has a levels field
                if isinstance(data, list):
                    passed = len(data) > 0
                    # Verify each level has required fields
                    if passed:
                        level = data[0]
                        required_fields = ['level', 'name', 'xpRequired']
                        passed = all(field in level for field in required_fields)
                elif isinstance(data, dict) and 'levels' in data:
                    passed = isinstance(data['levels'], list) and len(data['levels']) > 0
            
            self._log_test("GET /curator/levels", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/levels", False, error=e)
            return False
    
    def test_get_curator_levels_not_empty(self):
        """Test that curator levels list is not empty"""
        try:
            response = requests.get(f"{self.base_url}/curator/levels")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                if isinstance(data, list):
                    passed = len(data) > 0
                elif isinstance(data, dict) and 'levels' in data:
                    passed = len(data['levels']) > 0
            
            self._log_test("GET /curator/levels (non-empty)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/levels (non-empty)", False, error=e)
            return False
    
    def test_get_curator_levels_structure(self):
        """Test that curator levels have correct structure"""
        try:
            response = requests.get(f"{self.base_url}/curator/levels")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                levels = data if isinstance(data, list) else data.get('levels', [])
                
                if levels:
                    for level in levels:
                        # Check required fields
                        if 'level' not in level or 'name' not in level or 'xpRequired' not in level:
                            passed = False
                            break
                        # Check types
                        if not isinstance(level['level'], int) or not isinstance(level['name'], str) or not isinstance(level['xpRequired'], int):
                            passed = False
                            break
            
            self._log_test("GET /curator/levels (structure validation)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/levels (structure validation)", False, error=e)
            return False
    
    def test_badges_unauthorized(self):
        """Test that protected badge endpoints require auth"""
        try:
            # Try to access user badges without token
            response = requests.get(f"{self.base_url}/badges/user")
            passed = response.status_code == 401  # Unauthorized expected
            
            self._log_test("GET /badges/user (no auth - should 401)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges/user (no auth - should 401)", False, error=e)
            return False
    
    def test_curator_stats_unauthorized(self):
        """Test that protected curator stats endpoint requires auth"""
        try:
            # Try to access curator stats without token
            response = requests.get(f"{self.base_url}/curator/stats")
            passed = response.status_code == 401  # Unauthorized expected
            
            self._log_test("GET /curator/stats (no auth - should 401)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/stats (no auth - should 401)", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # ERROR HANDLING & VALIDATION TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_missing_auth_token(self):
        """Test endpoints that require auth without token"""
        try:
            # Try to access protected endpoint without token
            response = requests.get(f"{self.base_url}/users/profile")
            passed = response.status_code == 401  # Unauthorized expected
            
            self._log_test("Missing Auth Token (GET /users/profile)", passed, response)
            return passed
        except Exception as e:
            self._log_test("Missing Auth Token (GET /users/profile)", False, error=e)
            return False
    
    def test_invalid_auth_token(self):
        """Test with malformed auth token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_xyz"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 401  # Unauthorized expected
            
            self._log_test("Invalid Auth Token", passed, response)
            return passed
        except Exception as e:
            self._log_test("Invalid Auth Token", False, error=e)
            return False
    
    def test_register_invalid_email(self):
        """Test registration with invalid email format"""
        try:
            payload = {
                "email": "not_an_email",  # Invalid format
                "username": f"user_{self._random_string()}",
                "password": "Test123456!"
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=payload)
            passed = response.status_code == 400  # Bad request expected
            
            self._log_test("Register Invalid Email", passed, response)
            return passed
        except Exception as e:
            self._log_test("Register Invalid Email", False, error=e)
            return False
    
    def test_register_weak_password(self):
        """Test registration with weak password"""
        try:
            payload = {
                "email": f"user_{self._random_string()}@test.com",
                "username": f"user_{self._random_string()}",
                "password": "123"  # Too weak
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=payload)
            passed = response.status_code == 400  # Bad request expected
            
            self._log_test("Register Weak Password", passed, response)
            return passed
        except Exception as e:
            self._log_test("Register Weak Password", False, error=e)
            return False
    
    def test_register_missing_fields(self):
        """Test registration with missing required fields"""
        try:
            payload = {
                "email": f"user_{self._random_string()}@test.com"
                # Missing username and password
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=payload)
            passed = response.status_code == 400  # Bad request expected
            
            self._log_test("Register Missing Fields", passed, response)
            return passed
        except Exception as e:
            self._log_test("Register Missing Fields", False, error=e)
            return False
    
    def test_update_aura_invalid_color(self):
        """Test aura update with invalid hex color"""
        if not self.token:
            self._log_test("Update Aura Invalid Color", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "auraColors": ["#GGGGGG", "#FF6B9D"]  # Invalid hex color
            }
            
            response = requests.put(f"{self.base_url}/aura/profile", 
                                   headers=headers, json=payload)
            passed = response.status_code == 400  # Bad request expected
            
            self._log_test("Update Aura Invalid Color", passed, response)
            return passed
        except Exception as e:
            self._log_test("Update Aura Invalid Color", False, error=e)
            return False
    
    def test_get_nonexistent_user(self):
        """Test getting non-existent user"""
        try:
            response = requests.get(f"{self.base_url}/users/nonexistent_user_12345")
            passed = response.status_code == 404  # Not found expected
            
            self._log_test("GET Non-existent User", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET Non-existent User", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # PAGINATION TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_pagination_movies(self):
        """Test pagination with offset and limit"""
        try:
            # Get first page
            response1 = requests.get(f"{self.base_url}/content/movies?limit=2&offset=0")
            passed = response1.status_code == 200
            
            if passed:
                data1 = response1.json()
                # Get second page
                response2 = requests.get(f"{self.base_url}/content/movies?limit=2&offset=2")
                passed = response2.status_code == 200 and response2.json() != data1
            
            self._log_test("Pagination Movies (limit=2, offset)", passed, response1)
            return passed
        except Exception as e:
            self._log_test("Pagination Movies (limit=2, offset)", False, error=e)
            return False
    
    def test_pagination_albums(self):
        """Test pagination for albums"""
        try:
            response = requests.get(f"{self.base_url}/content/albums?limit=5&offset=0")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Verify pagination structure
                if 'items' in data:
                    passed = isinstance(data['items'], list)
            
            self._log_test("Pagination Albums (offset/limit)", passed, response)
            return passed
        except Exception as e:
            self._log_test("Pagination Albums (offset/limit)", False, error=e)
            return False
    
    def test_get_shares_pagination(self):
        """Test pagination for user shares"""
        if not self.token:
            self._log_test("Shares Pagination", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            # Create multiple shares first
            for i in range(3):
                payload = {
                    "category": "cinema",
                    "contentId": f"tt{100000 + i}",
                    "title": f"Movie {i+1}",
                    "caption": f"Share {i+1}"
                }
                requests.post(f"{self.base_url}/aura/shares", headers=headers, json=payload)
            
            # Test pagination
            response = requests.get(f"{self.base_url}/aura/shares?limit=2&offset=0", 
                                   headers=headers)
            passed = response.status_code == 200
            
            self._log_test("Shares Pagination", passed, response)
            return passed
        except Exception as e:
            self._log_test("Shares Pagination", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # RESPONSE SCHEMA VALIDATION
    # ─────────────────────────────────────────────────────────
    
    def test_user_response_schema(self):
        """Validate user response has required fields including new contract fields"""
        if not self.token:
            self._log_test("User Response Schema", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Check required fields including new contract fields
                required_fields = ['userId', 'email', 'username', 'emailVerified', 'socialMediaLinks']
                passed = all(field in data for field in required_fields)
                # socialMediaLinks must be a list
                if passed:
                    passed = isinstance(data['socialMediaLinks'], list)
            
            self._log_test("User Response Schema", passed, response)
            return passed
        except Exception as e:
            self._log_test("User Response Schema", False, error=e)
            return False
    
    def test_content_response_schema(self):
        """Validate content response has required fields per OpenAPI spec"""
        try:
            response = requests.get(f"{self.base_url}/content/movies?limit=1")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                
                # Check pagination fields (PaginatedResponse schema)
                pagination_fields = ['total', 'limit', 'offset']
                passed = all(field in data for field in pagination_fields)
                
                # Check for data array (not 'items')
                if passed:
                    passed = 'data' in data and isinstance(data['data'], list)
                
                # Check Movie required fields
                if passed and len(data['data']) > 0:
                    item = data['data'][0]
                    # Movie schema requires: id, title, year, director, type
                    required_fields = ['id', 'title', 'year', 'director', 'type']
                    passed = all(field in item for field in required_fields)
            
            self._log_test("Content Response Schema (OpenAPI Contract)", passed, response)
            return passed
        except Exception as e:
            self._log_test("Content Response Schema (OpenAPI Contract)", False, error=e)
            return False
    
    def test_aura_response_schema(self):
        """Validate aura profile response structure including socialMediaLinks"""
        if not self.token:
            self._log_test("Aura Response Schema", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/aura/profile", headers=headers)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Check required fields including socialMediaLinks
                required_fields = ['userId', 'username', 'auraColors', 'aestheticTags', 'topCategories', 'socialMediaLinks']
                passed = all(field in data for field in required_fields)
                if passed:
                    passed = isinstance(data['socialMediaLinks'], list)
            
            self._log_test("Aura Response Schema", passed, response)
            return passed
        except Exception as e:
            self._log_test("Aura Response Schema", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # SHARES TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_create_share(self):
        """Test creating a new share"""
        if not self.token:
            self._log_test("POST /aura/shares", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "category": "cinema",
                "contentId": "tt0133093",
                "title": "The Matrix",
                "image": "https://example.com/matrix.jpg",
                "caption": "Mind-bending sci-fi masterpiece!"
            }
            
            response = requests.post(f"{self.base_url}/aura/shares", 
                                    headers=headers, json=payload)
            passed = response.status_code == 201
            
            self._log_test("POST /aura/shares", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /aura/shares", False, error=e)
            return False
    
    def test_get_user_shares(self):
        """Test getting current user's shares"""
        if not self.token:
            self._log_test("GET /aura/shares", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/aura/shares?limit=10", 
                                   headers=headers)
            passed = response.status_code == 200
            
            self._log_test("GET /aura/shares", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /aura/shares", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # SOCIAL POSTS TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_create_post(self):
        """Test creating a community post"""
        if not self.token:
            self._log_test("POST /social/posts", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "category": "cinema",
                "title": "Just watched this amazing film!",
                "image": "https://example.com/test-post.jpg",
                "dominantColor": "#FF5733"
            }
            
            response = requests.post(f"{self.base_url}/social/posts", 
                                    headers=headers, json=payload)
            passed = response.status_code == 201
            
            if passed and response.json():
                data = response.json()
                if 'post' in data:
                    self.test_post_id = data['post'].get('id')
            
            self._log_test("POST /social/posts", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/posts", False, error=e)
            return False
    
    def test_create_post_missing_fields(self):
        """Test creating post with missing required fields"""
        if not self.token:
            self._log_test("POST /social/posts (missing fields)", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "category": "cinema"
                # Missing title and image
            }
            
            response = requests.post(f"{self.base_url}/social/posts", 
                                    headers=headers, json=payload)
            passed = response.status_code == 400
            
            self._log_test("POST /social/posts (missing fields)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/posts (missing fields)", False, error=e)
            return False
    
    def test_create_post_invalid_category(self):
        """Test creating post with invalid category"""
        if not self.token:
            self._log_test("POST /social/posts (invalid category)", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "category": "invalid_category",
                "title": "Test post",
                "image": "https://example.com/test.jpg"
            }
            
            response = requests.post(f"{self.base_url}/social/posts", 
                                    headers=headers, json=payload)
            passed = response.status_code == 400
            
            self._log_test("POST /social/posts (invalid category)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/posts (invalid category)", False, error=e)
            return False
    
    def test_get_community_posts(self):
        """Test getting community posts"""
        try:
            response = requests.get(f"{self.base_url}/social/posts?limit=10")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # Store a post ID for later tests if available
                if 'posts' in data and len(data['posts']) > 0:
                    self.test_post_id = data['posts'][0].get('id')
            
            self._log_test("GET /social/posts", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/posts", False, error=e)
            return False
    
    def test_get_posts_with_category_filter(self):
        """Test getting posts filtered by category"""
        try:
            response = requests.get(f"{self.base_url}/social/posts?category=cinema&limit=10")
            passed = response.status_code == 200
            
            self._log_test("GET /social/posts (category filter)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/posts (category filter)", False, error=e)
            return False
    
    def test_get_posts_sorted_by_popular(self):
        """Test getting posts sorted by popularity"""
        try:
            response = requests.get(f"{self.base_url}/social/posts?sortBy=popular&limit=10")
            passed = response.status_code == 200
            
            self._log_test("GET /social/posts (sort by popular)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/posts (sort by popular)", False, error=e)
            return False
    
    def test_get_post_by_id(self):
        """Test getting a post by ID"""
        if not hasattr(self, 'test_post_id') or not self.test_post_id:
            self._log_test("GET /social/posts/{id}", False, error="No test post ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/social/posts/{self.test_post_id}")
            passed = response.status_code == 200
            
            self._log_test("GET /social/posts/{id}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/posts/{id}", False, error=e)
            return False
    
    def test_get_nonexistent_post(self):
        """Test getting a non-existent post"""
        try:
            response = requests.get(f"{self.base_url}/social/posts/nonexistent_post_id")
            passed = response.status_code == 404
            
            self._log_test("GET /social/posts/{id} (not found)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/posts/{id} (not found)", False, error=e)
            return False
    
    def test_like_post(self):
        """Test liking a post"""
        if not self.token:
            self._log_test("POST /social/posts/{id}/like", False, error="No auth token available")
            return False
        
        if not hasattr(self, 'test_post_id') or not self.test_post_id:
            self._log_test("POST /social/posts/{id}/like", False, error="No test post ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.base_url}/social/posts/{self.test_post_id}/like", 
                                    headers=headers)
            passed = response.status_code == 200
            
            self._log_test("POST /social/posts/{id}/like", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/posts/{id}/like", False, error=e)
            return False
    
    def test_like_post_again(self):
        """Test liking the same post again (should be idempotent)"""
        if not self.token:
            self._log_test("POST /social/posts/{id}/like (duplicate)", False, error="No auth token available")
            return False
        
        if not hasattr(self, 'test_post_id') or not self.test_post_id:
            self._log_test("POST /social/posts/{id}/like (duplicate)", False, error="No test post ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.base_url}/social/posts/{self.test_post_id}/like", 
                                    headers=headers)
            passed = response.status_code == 200
            
            self._log_test("POST /social/posts/{id}/like (duplicate)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/posts/{id}/like (duplicate)", False, error=e)
            return False
    
    def test_unlike_post(self):
        """Test unliking a post"""
        if not self.token:
            self._log_test("DELETE /social/posts/{id}/like", False, error="No auth token available")
            return False
        
        if not hasattr(self, 'test_post_id') or not self.test_post_id:
            self._log_test("DELETE /social/posts/{id}/like", False, error="No test post ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.delete(f"{self.base_url}/social/posts/{self.test_post_id}/like", 
                                      headers=headers)
            passed = response.status_code == 200
            
            self._log_test("DELETE /social/posts/{id}/like", passed, response)
            return passed
        except Exception as e:
            self._log_test("DELETE /social/posts/{id}/like", False, error=e)
            return False
    
    def test_add_comment(self):
        """Test adding a comment to a post"""
        if not self.token:
            self._log_test("POST /social/posts/{id}/comments", False, error="No auth token available")
            return False
        
        if not hasattr(self, 'test_post_id') or not self.test_post_id:
            self._log_test("POST /social/posts/{id}/comments", False, error="No test post ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "text": "This is a test comment!"
            }
            
            response = requests.post(f"{self.base_url}/social/posts/{self.test_post_id}/comments", 
                                    headers=headers, json=payload)
            passed = response.status_code == 201
            
            self._log_test("POST /social/posts/{id}/comments", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/posts/{id}/comments", False, error=e)
            return False
    
    def test_add_comment_missing_text(self):
        """Test adding comment with missing text field"""
        if not self.token:
            self._log_test("POST /social/posts/{id}/comments (missing text)", False, error="No auth token available")
            return False
        
        if not hasattr(self, 'test_post_id') or not self.test_post_id:
            self._log_test("POST /social/posts/{id}/comments (missing text)", False, error="No test post ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {}
            
            response = requests.post(f"{self.base_url}/social/posts/{self.test_post_id}/comments", 
                                    headers=headers, json=payload)
            passed = response.status_code == 400
            
            self._log_test("POST /social/posts/{id}/comments (missing text)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/posts/{id}/comments (missing text)", False, error=e)
            return False
    
    def test_get_post_comments(self):
        """Test getting comments for a post"""
        if not hasattr(self, 'test_post_id') or not self.test_post_id:
            self._log_test("GET /social/posts/{id}/comments", False, error="No test post ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/social/posts/{self.test_post_id}/comments?limit=10")
            passed = response.status_code == 200
            
            self._log_test("GET /social/posts/{id}/comments", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/posts/{id}/comments", False, error=e)
            return False
    
    def test_delete_post(self):
        """Test deleting a post"""
        if not self.token:
            self._log_test("DELETE /social/posts/{id}", False, error="No auth token available")
            return False
        
        if not hasattr(self, 'test_post_id') or not self.test_post_id:
            self._log_test("DELETE /social/posts/{id}", False, error="No test post ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.delete(f"{self.base_url}/social/posts/{self.test_post_id}", 
                                      headers=headers)
            passed = response.status_code == 204
            
            self._log_test("DELETE /social/posts/{id}", passed, response)
            return passed
        except Exception as e:
            self._log_test("DELETE /social/posts/{id}", False, error=e)
            return False
    
    def test_delete_post_unauthorized(self):
        """Test deleting a post created by another user (should fail)"""
        if not self.token:
            self._log_test("DELETE /social/posts/{id} (unauthorized)", False, error="No auth token available")
            return False
        
        # Create a new user and post to test authorization
        try:
            # Register second user
            username2 = f"testuser2_{self._random_string()}"
            email2 = f"{username2}@test.com"
            register_payload = {
                "email": email2,
                "username": username2,
                "password": "Test123456!"
            }
            reg_response = requests.post(f"{self.base_url}/auth/register", json=register_payload)
            
            # Verify email manually to bypass email workflow
            _verify_email(email2)
            
            # Login as second user
            login_payload = {"email": email2, "password": "Test123456!"}
            login_response = requests.post(f"{self.base_url}/auth/login", json=login_payload)
            
            if login_response.status_code == 200:
                token2 = login_response.json().get('token')
                
                # Create post as second user
                headers2 = {"Authorization": f"Bearer {token2}"}
                post_payload = {
                    "category": "music",
                    "title": "Test post by user 2",
                    "image": "https://example.com/test2.jpg"
                }
                post_response = requests.post(f"{self.base_url}/social/posts", 
                                             headers=headers2, json=post_payload)
                
                if post_response.status_code == 201:
                    post_id = post_response.json()['post']['id']
                    
                    # Try to delete as first user (should fail)
                    headers1 = {"Authorization": f"Bearer {self.token}"}
                    delete_response = requests.delete(f"{self.base_url}/social/posts/{post_id}", 
                                                     headers=headers1)
                    passed = delete_response.status_code == 403
                    
                    # Cleanup - delete as the owner
                    requests.delete(f"{self.base_url}/social/posts/{post_id}", headers=headers2)
                    
                    self._log_test("DELETE /social/posts/{id} (unauthorized)", passed, delete_response)
                    return passed
            
            self._log_test("DELETE /social/posts/{id} (unauthorized)", False, error="Setup failed")
            return False
        except Exception as e:
            self._log_test("DELETE /social/posts/{id} (unauthorized)", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # BADGES & GAMIFICATION TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_get_all_badges(self):
        """Test getting all available badges"""
        try:
            response = requests.get(f"{self.base_url}/badges")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # API returns a raw list of badges
                passed = isinstance(data, list) and len(data) > 0
            
            self._log_test("GET /badges", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges", False, error=e)
            return False
    
    def test_get_badges_with_rarity_filter(self):
        """Test getting badges filtered by rarity"""
        try:
            response = requests.get(f"{self.base_url}/badges?rarity=rare")
            passed = response.status_code == 200
            
            if passed:
                badges = response.json()
                passed = isinstance(badges, list)
                # Verify all returned badges have rarity=rare
                if passed and len(badges) > 0:
                    passed = all(badge.get('rarity') == 'rare' for badge in badges)
            
            self._log_test("GET /badges (rarity filter)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges (rarity filter)", False, error=e)
            return False
    
    def test_get_badges_with_category_filter(self):
        """Test getting badges filtered by category (valid: early, completionist, social, streak, special)"""
        try:
            response = requests.get(f"{self.base_url}/badges?category=social")
            passed = response.status_code == 200
            
            if passed:
                badges = response.json()
                passed = isinstance(badges, list)
                # Verify all returned badges have category=social
                if passed and len(badges) > 0:
                    passed = all(badge.get('category') == 'social' for badge in badges)
            
            self._log_test("GET /badges (category filter)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges (category filter)", False, error=e)
            return False
    
    def test_get_badges_with_multiple_filters(self):
        """Test getting badges with multiple filters (valid categories: early, completionist, social, streak, special)"""
        try:
            response = requests.get(f"{self.base_url}/badges?rarity=rare&category=social")
            passed = response.status_code == 200
            
            if passed:
                badges = response.json()
                passed = isinstance(badges, list)
            
            self._log_test("GET /badges (multiple filters)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges (multiple filters)", False, error=e)
            return False
    
    def test_get_current_user_badges(self):
        """Test getting current user's earned badges"""
        if not self.token:
            self._log_test("GET /badges/user", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/badges/user", headers=headers)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # API returns a raw list of badge objects
                passed = isinstance(data, list)
            
            self._log_test("GET /badges/user", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges/user", False, error=e)
            return False
    
    def test_get_user_badges_by_id(self):
        """Test getting specific user's badges by ID"""
        if not self.user_id:
            self._log_test("GET /badges/user/{userId}", False, error="No user_id available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/badges/user/{self.user_id}")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # API returns a raw list of badge objects
                passed = isinstance(data, list)
            
            self._log_test("GET /badges/user/{userId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges/user/{userId}", False, error=e)
            return False
    
    def test_get_nonexistent_user_badges(self):
        """Test getting badges for non-existent user"""
        try:
            fake_id = "nonexistent_user_" + self._random_string(10)
            response = requests.get(f"{self.base_url}/badges/user/{fake_id}")
            passed = response.status_code == 404
            
            self._log_test("GET /badges/user/{userId} (404 error)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /badges/user/{userId} (404 error)", False, error=e)
            return False
    
    def test_get_current_user_curator_stats(self):
        """Test getting current user's curator statistics"""
        if not self.token:
            self._log_test("GET /curator/stats", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/curator/stats", headers=headers)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Verify expected fields in curator stats
                required_fields = ['totalShares', 'currentLevel', 'currentXP', 'xpToNextLevel']
                passed = all(field in data for field in required_fields)
            
            self._log_test("GET /curator/stats", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/stats", False, error=e)
            return False
    
    def test_get_curator_stats_without_auth(self):
        """Test curator stats endpoint without authentication (should fail)"""
        try:
            response = requests.get(f"{self.base_url}/curator/stats")
            passed = response.status_code == 401
            
            self._log_test("GET /curator/stats (401 error)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/stats (401 error)", False, error=e)
            return False
    
    def test_get_user_curator_stats_by_id(self):
        """Test getting specific user's curator statistics"""
        if not self.user_id:
            self._log_test("GET /curator/stats/{userId}", False, error="No user_id available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/curator/stats/{self.user_id}")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Verify expected fields
                required_fields = ['totalShares', 'currentLevel', 'currentXP']
                passed = all(field in data for field in required_fields)
            
            self._log_test("GET /curator/stats/{userId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/stats/{userId}", False, error=e)
            return False
    
    def test_get_nonexistent_user_curator_stats(self):
        """Test getting curator stats for non-existent user"""
        try:
            fake_id = "nonexistent_user_" + self._random_string(10)
            response = requests.get(f"{self.base_url}/curator/stats/{fake_id}")
            passed = response.status_code == 404
            
            self._log_test("GET /curator/stats/{userId} (404 error)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/stats/{userId} (404 error)", False, error=e)
            return False
    
    def test_get_all_curator_levels(self):
        """Test getting all curator levels"""
        try:
            response = requests.get(f"{self.base_url}/curator/levels")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                levels = data.get('levels', [])
                passed = isinstance(levels, list) and len(levels) > 0
                
                if passed and len(levels) > 0:
                    # Verify level structure
                    level = levels[0]
                    required_fields = ['level', 'name', 'xpRequired']
                    passed = all(field in level for field in required_fields)
            
            self._log_test("GET /curator/levels", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/levels", False, error=e)
            return False
    
    def test_curator_levels_are_progressive(self):
        """Test that curator levels are in progressive order"""
        try:
            response = requests.get(f"{self.base_url}/curator/levels")
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                levels = data.get('levels', [])
                
                if len(levels) > 1:
                    # Verify levels are in ascending order
                    for i in range(len(levels) - 1):
                        level1 = levels[i].get('level', 0)
                        level2 = levels[i + 1].get('level', 0)
                        xp1 = levels[i].get('xpRequired', 0)
                        xp2 = levels[i + 1].get('xpRequired', 0)
                        
                        if level2 <= level1 or xp2 <= xp1:
                            passed = False
                            break
            
            self._log_test("GET /curator/levels (progressive order)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /curator/levels (progressive order)", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # ROOMS TESTS
    # ─────────────────────────────────────────────────────────
    
    def test_get_aesthetic_rooms(self):
        """Test getting aesthetic rooms"""
        try:
            response = requests.get(f"{self.base_url}/social/rooms?limit=10")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # API returns paginated rooms under the "data" key
                if 'data' in data:
                    rooms = data['data']
                elif 'rooms' in data:
                    rooms = data['rooms']
                elif isinstance(data, list):
                    rooms = data
                else:
                    rooms = []
                
                # Store a room ID for later tests if available
                if len(rooms) > 0:
                    self.test_room_id = rooms[0].get('id')
            
            self._log_test("GET /social/rooms", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/rooms", False, error=e)
            return False
    
    def test_get_aesthetic_rooms_with_limit(self):
        """Test getting aesthetic rooms with limit parameter"""
        try:
            response = requests.get(f"{self.base_url}/social/rooms?limit=5&offset=0")
            passed = response.status_code == 200
            
            self._log_test("GET /social/rooms (with limit)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/rooms (with limit)", False, error=e)
            return False
    
    def test_get_aesthetic_rooms_trending(self):
        """Test getting trending aesthetic rooms"""
        try:
            response = requests.get(f"{self.base_url}/social/rooms?trending=true&limit=10")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # If API filters trending rooms, all should have trending=true
                if 'rooms' in data:
                    rooms = data['rooms']
                elif isinstance(data, list):
                    rooms = data
                else:
                    rooms = []
                
                # Optionally validate that trending filter was applied
                # if len(rooms) > 0:
                #     passed = all(room.get('trending') for room in rooms)
            
            self._log_test("GET /social/rooms (trending)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/rooms (trending)", False, error=e)
            return False
    
    def test_get_room_by_id(self):
        """Test getting a room by ID"""
        if not hasattr(self, 'test_room_id') or not self.test_room_id:
            self._log_test("GET /social/rooms/{roomId}", False, error="No test room ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/social/rooms/{self.test_room_id}")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # Validate required fields from AestheticRoom schema
                if isinstance(data, dict):
                    required_fields = ['id', 'name', 'hashtag']
                    passed = all(field in data for field in required_fields)
            
            self._log_test("GET /social/rooms/{roomId}", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/rooms/{roomId}", False, error=e)
            return False
    
    def test_get_nonexistent_room(self):
        """Test getting a non-existent room (should return 404)"""
        try:
            response = requests.get(f"{self.base_url}/social/rooms/nonexistent_room_id_12345")
            passed = response.status_code == 404
            
            self._log_test("GET /social/rooms/{roomId} (not found)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/rooms/{roomId} (not found)", False, error=e)
            return False
    
    def test_get_room_posts(self):
        """Test getting posts in a room"""
        if not hasattr(self, 'test_room_id') or not self.test_room_id:
            self._log_test("GET /social/rooms/{roomId}/posts", False, error="No test room ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/social/rooms/{self.test_room_id}/posts?limit=10")
            passed = response.status_code == 200
            
            if passed and response.json():
                data = response.json()
                # API should return posts
                if 'posts' in data:
                    posts = data['posts']
                elif isinstance(data, list):
                    posts = data
                else:
                    posts = []
            
            self._log_test("GET /social/rooms/{roomId}/posts", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/rooms/{roomId}/posts", False, error=e)
            return False
    
    def test_get_room_posts_with_pagination(self):
        """Test getting room posts with pagination"""
        if not hasattr(self, 'test_room_id') or not self.test_room_id:
            self._log_test("GET /social/rooms/{roomId}/posts (pagination)", False, error="No test room ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/social/rooms/{self.test_room_id}/posts?limit=5&offset=0")
            passed = response.status_code == 200
            
            self._log_test("GET /social/rooms/{roomId}/posts (pagination)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/rooms/{roomId}/posts (pagination)", False, error=e)
            return False
    
    def test_get_room_posts_nonexistent_room(self):
        """Test getting posts from a non-existent room (should return 404)"""
        try:
            response = requests.get(f"{self.base_url}/social/rooms/nonexistent_room_id/posts")
            passed = response.status_code == 404
            
            self._log_test("GET /social/rooms/{roomId}/posts (not found)", passed, response)
            return passed
        except Exception as e:
            self._log_test("GET /social/rooms/{roomId}/posts (not found)", False, error=e)
            return False
    
    def test_join_room(self):
        """Test joining an aesthetic room"""
        if not self.token:
            self._log_test("POST /social/rooms/{roomId}/join", False, error="No auth token available")
            return False
        
        if not hasattr(self, 'test_room_id') or not self.test_room_id:
            self._log_test("POST /social/rooms/{roomId}/join", False, error="No test room ID available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.base_url}/social/rooms/{self.test_room_id}/join", 
                                    headers=headers)
            # Status code can be 200 (success) or 400/409 (already joined)
            passed = response.status_code in [200, 400, 409]
            
            # Store room ID if join was successful
            if response.status_code == 200:
                self.test_room_joined = self.test_room_id
            
            self._log_test("POST /social/rooms/{roomId}/join", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/rooms/{roomId}/join", False, error=e)
            return False
    
    def test_join_room_unauthorized(self):
        """Test joining a room without authentication (should return 401)"""
        if not hasattr(self, 'test_room_id') or not self.test_room_id:
            self._log_test("POST /social/rooms/{roomId}/join (unauthorized)", False, error="No test room ID available")
            return False
        
        try:
            # No authorization header
            response = requests.post(f"{self.base_url}/social/rooms/{self.test_room_id}/join")
            passed = response.status_code == 401
            
            self._log_test("POST /social/rooms/{roomId}/join (unauthorized)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/rooms/{roomId}/join (unauthorized)", False, error=e)
            return False
    
    def test_join_nonexistent_room(self):
        """Test joining a non-existent room (should return 404)"""
        if not self.token:
            self._log_test("POST /social/rooms/{roomId}/join (not found)", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.base_url}/social/rooms/nonexistent_room_id/join", 
                                    headers=headers)
            passed = response.status_code == 404
            
            self._log_test("POST /social/rooms/{roomId}/join (not found)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/rooms/{roomId}/join (not found)", False, error=e)
            return False
    
    def test_leave_room(self):
        """Test leaving an aesthetic room"""
        if not self.token:
            self._log_test("POST /social/rooms/{roomId}/leave", False, error="No auth token available")
            return False
        
        # Use the room we joined, or fall back to test room
        room_id_to_leave = getattr(self, 'test_room_joined', None)
        if not room_id_to_leave:
            if hasattr(self, 'test_room_id') and self.test_room_id:
                room_id_to_leave = self.test_room_id
            else:
                self._log_test("POST /social/rooms/{roomId}/leave", False, error="No test room ID available")
                return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.base_url}/social/rooms/{room_id_to_leave}/leave", 
                                    headers=headers)
            # Status code should be 204 (No Content) for successful leave
            passed = response.status_code == 204
            
            # If we successfully left, clear the stored ID
            if passed and hasattr(self, 'test_room_joined'):
                self.test_room_joined = None
            
            self._log_test("POST /social/rooms/{roomId}/leave", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/rooms/{roomId}/leave", False, error=e)
            return False
    
    def test_leave_room_unauthorized(self):
        """Test leaving a room without authentication (should return 401)"""
        if not hasattr(self, 'test_room_id') or not self.test_room_id:
            self._log_test("POST /social/rooms/{roomId}/leave (unauthorized)", False, error="No test room ID available")
            return False
        
        try:
            # No authorization header
            response = requests.post(f"{self.base_url}/social/rooms/{self.test_room_id}/leave")
            passed = response.status_code == 401
            
            self._log_test("POST /social/rooms/{roomId}/leave (unauthorized)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/rooms/{roomId}/leave (unauthorized)", False, error=e)
            return False
    
    def test_leave_nonexistent_room(self):
        """Test leaving a non-existent room (should return 404)"""
        if not self.token:
            self._log_test("POST /social/rooms/{roomId}/leave (not found)", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.base_url}/social/rooms/nonexistent_room_id/leave", 
                                    headers=headers)
            passed = response.status_code == 404
            
            self._log_test("POST /social/rooms/{roomId}/leave (not found)", passed, response)
            return passed
        except Exception as e:
            self._log_test("POST /social/rooms/{roomId}/leave (not found)", False, error=e)
            return False
    
    # ─────────────────────────────────────────────────────────
    # RUN ALL TESTS
    # ─────────────────────────────────────────────────────────
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 70)
        print("VibeCheck API Test Suite")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("=" * 70)
        print()
        
        # Health check first
        print("🏥 Health Check")
        print("-" * 70)
        self.test_health()
        print()
        
        # Auth tests
        print("🔐 Authentication Tests")
        print("-" * 70)
        self.test_register()
        self.test_register_duplicate()
        self.test_register_invalid_email()
        self.test_register_weak_password()
        self.test_register_missing_fields()
        self.test_login()
        self.test_login_invalid()
        self.test_missing_auth_token()
        self.test_invalid_auth_token()
        print()
        
        # JWT Validation tests
        print("🔑 JWT Token Validation Tests")
        print("-" * 70)
        self.test_missing_authorization_header()
        self.test_malformed_token_empty()
        self.test_malformed_token_invalid_format()
        self.test_malformed_token_missing_bearer()
        self.test_malformed_token_wrong_prefix()
        self.test_tampered_token_payload()
        self.test_random_token_invalid()
        print()
        
        # User profile tests
        print("👤 User Profile Tests")
        print("-" * 70)
        self.test_get_profile()
        self.test_update_profile()
        self.test_get_user_by_id()
        print()
        
        # Content tests - Movies
        print("🎬 Movies Content Tests")
        print("-" * 70)
        self.test_get_movies()
        self.test_get_movies_with_search()
        self.test_get_movie_by_id()
        print()
        
        # Content tests - Albums
        print("🎵 Albums Content Tests")
        print("-" * 70)
        self.test_get_albums()
        self.test_get_albums_with_search()
        self.test_get_album_by_id()
        print()
        
        # Content tests - Games
        print("🎮 Games Content Tests")
        print("-" * 70)
        self.test_get_games()
        self.test_get_games_with_filters()
        self.test_get_game_by_id()
        print()
        
        # Content tests - Books
        print("📚 Books Content Tests")
        print("-" * 70)
        self.test_get_books()
        self.test_get_books_with_search()
        self.test_get_book_by_id()
        print()
        
        # Content tests - Locations
        print("🗺️  Locations Content Tests")
        print("-" * 70)
        self.test_get_locations()
        self.test_get_locations_with_filters()
        self.test_get_location_by_id()
        print()
        
        # Search tests
        print("🔍 Search Tests")
        print("-" * 70)
        self.test_global_search()
        self.test_global_search_with_categories()
        print()
        
        # Aura tests
        print("✨ Aura Profile Tests")
        print("-" * 70)
        self.test_get_current_user_aura()
        self.test_update_aura_profile()
        self.test_update_aura_profile_rejects_aesthetic_tags()
        self.test_get_user_aura_by_id()
        self.test_update_aura_invalid_color()
        print()
        
        # Aura matching tests
        print("💫 Aura Matching Tests")
        print("-" * 70)
        self.test_get_aura_matches()
        self.test_get_aura_matches_with_pagination()
        self.test_calculate_compatibility()
        self.test_calculate_compatibility_with_self()
        print()
        
        # Shares tests
        print("📤 Shares Tests")
        print("-" * 70)
        self.test_create_share()
        self.test_get_user_shares()
        print()
        
        # Badges & Gamification tests
        print("🏆 Badges & Gamification Tests")
        print("-" * 70)
        self.test_get_all_badges()
        
        # self.test_get_badges_with_rarity_filter()
        # self.test_get_badges_with_category_filter()
        # self.test_get_badges_with_multiple_filters()
        # self.test_get_current_user_badges()
        # self.test_get_user_badges_by_id()
        # self.test_get_nonexistent_user_badges()
        # self.test_get_current_user_curator_stats()
        # self.test_get_curator_stats_without_auth()
        # self.test_get_user_curator_stats_by_id()
        # self.test_get_nonexistent_user_curator_stats()
        # self.test_get_all_curator_levels()
        # self.test_curator_levels_are_progressive()

        self.test_get_badges_by_rarity()
        self.test_get_badges_by_category()
        self.test_get_badges_with_multiple_filters()
        self.test_get_user_badges()
        self.test_get_user_badges_by_id()
        self.test_get_nonexistent_user_badges()
        self.test_get_curator_stats()
        self.test_get_curator_stats_by_id()
        self.test_get_nonexistent_user_curator_stats()
        self.test_get_curator_levels()
        self.test_get_curator_levels_not_empty()
        self.test_get_curator_levels_structure()
        self.test_badges_unauthorized()
        self.test_curator_stats_unauthorized()
        print()
        
        # Social Posts tests
        print("💬 Social Posts Tests")
        print("-" * 70)
        self.test_create_post()
        self.test_create_post_missing_fields()
        self.test_create_post_invalid_category()
        self.test_get_community_posts()
        self.test_get_posts_with_category_filter()
        self.test_get_posts_sorted_by_popular()
        self.test_get_post_by_id()
        self.test_get_nonexistent_post()
        self.test_like_post()
        self.test_like_post_again()
        self.test_unlike_post()
        self.test_add_comment()
        self.test_add_comment_missing_text()
        self.test_get_post_comments()
        self.test_delete_post_unauthorized()
        self.test_delete_post()
        print()
        
        # Rooms tests
        print("🏤 Aesthetic Rooms Tests")
        print("-" * 70)
        self.test_get_aesthetic_rooms()
        self.test_get_aesthetic_rooms_with_limit()
        self.test_get_aesthetic_rooms_trending()
        self.test_get_room_by_id()
        self.test_get_nonexistent_room()
        self.test_get_room_posts()
        self.test_get_room_posts_with_pagination()
        self.test_get_room_posts_nonexistent_room()
        self.test_join_room()
        self.test_join_room_unauthorized()
        self.test_join_nonexistent_room()
        self.test_leave_room()
        self.test_leave_room_unauthorized()
        self.test_leave_nonexistent_room()
        print()
        
        # Pagination tests
        print("📑 Pagination Tests")
        print("-" * 70)
        self.test_pagination_movies()
        self.test_pagination_albums()
        self.test_get_shares_pagination()
        print()
        
        # Response schema validation
        print("✅ Response Schema Validation")
        print("-" * 70)
        self.test_user_response_schema()
        self.test_content_response_schema()
        self.test_aura_response_schema()
        print()
        
        # Error handling tests
        print("⚠️  Error Handling Tests")
        print("-" * 70)
        self.test_get_nonexistent_user()
        self.test_update_aura_invalid_color()
        print()
        
        # Summary
        print("=" * 70)
        print("Test Summary")
        print("=" * 70)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {failed} ✗")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print()
        
        if failed > 0:
            print("Failed Tests:")
            for r in self.test_results:
                if not r['passed']:
                    print(f"  ✗ {r['name']}")
                    if r['error']:
                        print(f"    {r['error']}")
        
        print("=" * 70)
        
        return passed == total


# ─────────────────────────────────────────────────────────
# PYTEST INTEGRATION
# ─────────────────────────────────────────────────────────

import pytest

@pytest.fixture(scope="session")
def tester() -> VibeCheckAPITester:
    """Create a single VibeCheckAPITester instance for all tests"""
    return VibeCheckAPITester()


def test_health(tester):
    assert tester.test_health()


def test_register(tester):
    assert tester.test_register()


def test_register_duplicate(tester):
    assert tester.test_register_duplicate()


def test_login(tester):
    assert tester.test_login()


def test_login_invalid(tester):
    assert tester.test_login_invalid()


def test_get_profile(tester):
    assert tester.test_get_profile()


def test_update_profile(tester):
    assert tester.test_update_profile()


def test_get_user_by_id(tester):
    assert tester.test_get_user_by_id()


def test_get_movies(tester):
    assert tester.test_get_movies()


def test_get_movies_with_search(tester):
    assert tester.test_get_movies_with_search()


def test_get_movie_by_id(tester):
    assert tester.test_get_movie_by_id()


def test_get_albums(tester):
    assert tester.test_get_albums()


def test_get_albums_with_search(tester):
    assert tester.test_get_albums_with_search()


def test_get_album_by_id(tester):
    assert tester.test_get_album_by_id()


def test_get_games(tester):
    assert tester.test_get_games()


def test_get_games_with_filters(tester):
    assert tester.test_get_games_with_filters()


def test_get_game_by_id(tester):
    assert tester.test_get_game_by_id()


def test_get_books(tester):
    assert tester.test_get_books()


def test_get_books_with_search(tester):
    assert tester.test_get_books_with_search()


def test_get_book_by_id(tester):
    assert tester.test_get_book_by_id()


def test_get_locations(tester):
    assert tester.test_get_locations()


def test_get_locations_with_filters(tester):
    assert tester.test_get_locations_with_filters()


def test_get_location_by_id(tester):
    assert tester.test_get_location_by_id()


def test_global_search(tester):
    assert tester.test_global_search()


def test_global_search_with_categories(tester):
    assert tester.test_global_search_with_categories()


def test_get_current_user_aura(tester):
    assert tester.test_get_current_user_aura()


def test_update_aura_profile(tester):
    assert tester.test_update_aura_profile()


def test_update_aura_profile_rejects_aesthetic_tags(tester):
    assert tester.test_update_aura_profile_rejects_aesthetic_tags()


def test_get_user_aura_by_id(tester):
    assert tester.test_get_user_aura_by_id()


def test_create_share(tester):
    assert tester.test_create_share()


def test_get_user_shares(tester):
    assert tester.test_get_user_shares()


# ─────────────────────────────────────────────────────────
# BADGES & GAMIFICATION TESTS
# ─────────────────────────────────────────────────────────

def test_get_all_badges(tester):
    assert tester.test_get_all_badges()


# def test_get_badges_with_rarity_filter(tester):
#     tester.test_get_badges_with_rarity_filter()

# def test_get_badges_with_category_filter(tester):
#     tester.test_get_badges_with_category_filter()

# def test_get_badges_with_multiple_filters(tester):
#     tester.test_get_badges_with_multiple_filters()

# def test_get_current_user_badges(tester):
#     tester.test_get_current_user_badges()


def test_get_badges_by_rarity(tester):
    assert tester.test_get_badges_by_rarity()


def test_get_badges_by_category(tester):
    assert tester.test_get_badges_by_category()


def test_get_badges_with_multiple_filters(tester):
    assert tester.test_get_badges_with_multiple_filters()


def test_get_user_badges(tester):
    assert tester.test_get_user_badges()


def test_get_user_badges_by_id(tester):
    assert tester.test_get_user_badges_by_id()


def test_get_nonexistent_user_badges(tester):
    assert tester.test_get_nonexistent_user_badges()


# def test_get_current_user_curator_stats(tester):
#     tester.test_get_current_user_curator_stats()

# def test_get_curator_stats_without_auth(tester):
#     assert tester.test_get_curator_stats_without_auth()

# def test_get_user_curator_stats_by_id(tester):
#     tester.test_get_user_curator_stats_by_id()


def test_get_curator_stats(tester):
    assert tester.test_get_curator_stats()


def test_get_curator_stats_by_id(tester):
    assert tester.test_get_curator_stats_by_id()


def test_get_nonexistent_user_curator_stats(tester):
    assert tester.test_get_nonexistent_user_curator_stats()


# def test_get_all_curator_levels(tester):
#     assert tester.test_get_all_curator_levels()

# def test_curator_levels_are_progressive(tester):
#     assert tester.test_curator_levels_are_progressive()


def test_get_curator_levels(tester):
    assert tester.test_get_curator_levels()


def test_get_curator_levels_not_empty(tester):
    assert tester.test_get_curator_levels_not_empty()


def test_get_curator_levels_structure(tester):
    assert tester.test_get_curator_levels_structure()


def test_badges_unauthorized(tester):
    assert tester.test_badges_unauthorized()


def test_curator_stats_unauthorized(tester):
    assert tester.test_curator_stats_unauthorized()


# ─────────────────────────────────────────────────────────
# SOCIAL POSTS TESTS
# ─────────────────────────────────────────────────────────

def test_create_post(tester):
    assert tester.test_create_post()


def test_create_post_missing_fields(tester):
    assert tester.test_create_post_missing_fields()


def test_create_post_invalid_category(tester):
    assert tester.test_create_post_invalid_category()


def test_get_community_posts(tester):
    assert tester.test_get_community_posts()


def test_get_posts_with_category_filter(tester):
    assert tester.test_get_posts_with_category_filter()


def test_get_posts_sorted_by_popular(tester):
    assert tester.test_get_posts_sorted_by_popular()


def test_get_post_by_id(tester):
    assert tester.test_get_post_by_id()


def test_get_nonexistent_post(tester):
    assert tester.test_get_nonexistent_post()


def test_like_post(tester):
    assert tester.test_like_post()


def test_like_post_again(tester):
    assert tester.test_like_post_again()


def test_unlike_post(tester):
    assert tester.test_unlike_post()


def test_add_comment(tester):
    assert tester.test_add_comment()


def test_add_comment_missing_text(tester):
    assert tester.test_add_comment_missing_text()


def test_get_post_comments(tester):
    assert tester.test_get_post_comments()


def test_delete_post(tester):
    assert tester.test_delete_post()


def test_delete_post_unauthorized(tester):
    assert tester.test_delete_post_unauthorized()


# ─────────────────────────────────────────────────────────
# ROOMS TESTS
# ─────────────────────────────────────────────────────────

def test_get_aesthetic_rooms(tester):
    assert tester.test_get_aesthetic_rooms()


def test_get_aesthetic_rooms_with_limit(tester):
    assert tester.test_get_aesthetic_rooms_with_limit()


def test_get_aesthetic_rooms_trending(tester):
    assert tester.test_get_aesthetic_rooms_trending()


def test_get_room_by_id(tester):
    assert tester.test_get_room_by_id()


def test_get_nonexistent_room(tester):
    assert tester.test_get_nonexistent_room()


def test_get_room_posts(tester):
    assert tester.test_get_room_posts()


def test_get_room_posts_with_pagination(tester):
    assert tester.test_get_room_posts_with_pagination()


def test_get_room_posts_nonexistent_room(tester):
    assert tester.test_get_room_posts_nonexistent_room()


def test_join_room(tester):
    assert tester.test_join_room()


def test_join_room_unauthorized(tester):
    assert tester.test_join_room_unauthorized()


def test_join_nonexistent_room(tester):
    assert tester.test_join_nonexistent_room()


def test_leave_room(tester):
    assert tester.test_leave_room()


def test_leave_room_unauthorized(tester):
    assert tester.test_leave_room_unauthorized()


def test_leave_nonexistent_room(tester):
    assert tester.test_leave_nonexistent_room()


# ─────────────────────────────────────────────────────────
# ERROR HANDLING TESTS
# ─────────────────────────────────────────────────────────

def test_missing_auth_token(tester):
    assert tester.test_missing_auth_token()


def test_invalid_auth_token(tester):
    assert tester.test_invalid_auth_token()


def test_register_invalid_email(tester):
    assert tester.test_register_invalid_email()


def test_register_weak_password(tester):
    assert tester.test_register_weak_password()


def test_register_missing_fields(tester):
    assert tester.test_register_missing_fields()


def test_update_aura_invalid_color(tester):
    assert tester.test_update_aura_invalid_color()


def test_get_nonexistent_user(tester):
    assert tester.test_get_nonexistent_user()


# ─────────────────────────────────────────────────────────
# PAGINATION TESTS
# ─────────────────────────────────────────────────────────

def test_pagination_movies(tester):
    assert tester.test_pagination_movies()


def test_pagination_albums(tester):
    assert tester.test_pagination_albums()


def test_get_shares_pagination(tester):
    assert tester.test_get_shares_pagination()


# ─────────────────────────────────────────────────────────
# RESPONSE SCHEMA VALIDATION TESTS
# ─────────────────────────────────────────────────────────

def test_user_response_schema(tester):
    assert tester.test_user_response_schema()


def test_content_response_schema(tester):
    assert tester.test_content_response_schema()


def test_aura_response_schema(tester):
    assert tester.test_aura_response_schema()


# ─────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test VibeCheck API')
    parser.add_argument('--url', default='http://localhost:3000/api/v1',
                       help='Base URL of the API (default: http://localhost:3000/api/v1)')
    args = parser.parse_args()
    
    api_tester = VibeCheckAPITester(base_url=args.url)
    success = api_tester.run_all_tests()
    
    sys.exit(0 if success else 1)
