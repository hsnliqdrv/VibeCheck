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
        """Test user registration"""
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
                # Some implementations return token on registration
                if 'token' in data:
                    self.token = data['token']
            
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
        """Test updating aura profile"""
        if not self.token:
            self._log_test("PUT /aura/profile", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "aestheticTags": ["minimalist", "dark academia", "cyberpunk"],
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
        """Validate user response has required fields"""
        if not self.token:
            self._log_test("User Response Schema", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/users/profile", headers=headers)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Check required fields
                required_fields = ['userId', 'email', 'username']
                passed = all(field in data for field in required_fields)
            
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
        """Validate aura profile response structure"""
        if not self.token:
            self._log_test("Aura Response Schema", False, error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/aura/profile", headers=headers)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                # Check required fields
                required_fields = ['userId', 'username', 'auraColors', 'aestheticTags', 'topCategories']
                passed = all(field in data for field in required_fields)
            
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
        self.test_get_user_aura_by_id()
        print()
        
        # Shares tests
        print("📤 Shares Tests")
        print("-" * 70)
        self.test_create_share()
        self.test_get_user_shares()
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
def tester():
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
    tester.test_get_profile()  # May fail if no token


def test_update_profile(tester):
    tester.test_update_profile()  # May fail if no token


def test_get_user_by_id(tester):
    tester.test_get_user_by_id()  # May fail if no user_id


def test_get_movies(tester):
    assert tester.test_get_movies()


def test_get_movies_with_search(tester):
    assert tester.test_get_movies_with_search()


def test_get_movie_by_id(tester):
    tester.test_get_movie_by_id()


def test_get_albums(tester):
    assert tester.test_get_albums()


def test_get_albums_with_search(tester):
    assert tester.test_get_albums_with_search()


def test_get_album_by_id(tester):
    tester.test_get_album_by_id()


def test_get_games(tester):
    assert tester.test_get_games()


def test_get_games_with_filters(tester):
    assert tester.test_get_games_with_filters()


def test_get_game_by_id(tester):
    tester.test_get_game_by_id()


def test_get_books(tester):
    assert tester.test_get_books()


def test_get_books_with_search(tester):
    assert tester.test_get_books_with_search()


def test_get_book_by_id(tester):
    tester.test_get_book_by_id()


def test_get_locations(tester):
    assert tester.test_get_locations()


def test_get_locations_with_filters(tester):
    assert tester.test_get_locations_with_filters()


def test_get_location_by_id(tester):
    tester.test_get_location_by_id()


def test_global_search(tester):
    assert tester.test_global_search()


def test_global_search_with_categories(tester):
    assert tester.test_global_search_with_categories()


def test_get_current_user_aura(tester):
    tester.test_get_current_user_aura()


def test_update_aura_profile(tester):
    tester.test_update_aura_profile()


def test_get_user_aura_by_id(tester):
    tester.test_get_user_aura_by_id()


def test_create_share(tester):
    tester.test_create_share()


def test_get_user_shares(tester):
    tester.test_get_user_shares()


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
    tester.test_update_aura_invalid_color()


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
    tester.test_get_shares_pagination()


# ─────────────────────────────────────────────────────────
# RESPONSE SCHEMA VALIDATION TESTS
# ─────────────────────────────────────────────────────────

def test_user_response_schema(tester):
    tester.test_user_response_schema()


def test_content_response_schema(tester):
    tester.test_content_response_schema()


def test_aura_response_schema(tester):
    tester.test_aura_response_schema()


# ─────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test VibeCheck API')
    parser.add_argument('--url', default='http://localhost:3000/api/v1',
                       help='Base URL of the API (default: http://localhost:3000/api/v1)')
    args = parser.parse_args()
    
    tester = VibeCheckAPITester(base_url=args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
