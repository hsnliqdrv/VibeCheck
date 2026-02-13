# VibeCheck API Testing

Comprehensive test suite for the VibeCheck backend API based on the OpenAPI specification.

## 📋 Test Coverage

The test suite covers all 17 MVP endpoints:

### Authentication (4 tests)
- ✅ POST `/auth/register` - User registration
- ✅ POST `/auth/register` - Duplicate email validation
- ✅ POST `/auth/login` - User login
- ✅ POST `/auth/login` - Invalid credentials check

### User Profile (3 tests)
- ✅ GET `/users/profile` - Get current user profile
- ✅ PUT `/users/profile` - Update user profile
- ✅ GET `/users/{userId}` - Get user by ID

### Content - Movies (3 tests)
- ✅ GET `/content/movies` - List movies
- ✅ GET `/content/movies?search=...` - Search movies
- ✅ GET `/content/movies/{movieId}` - Get movie details

### Content - Albums (3 tests)
- ✅ GET `/content/albums` - List albums
- ✅ GET `/content/albums?search=...` - Search albums
- ✅ GET `/content/albums/{albumId}` - Get album details

### Content - Games (3 tests)
- ✅ GET `/content/games` - List games
- ✅ GET `/content/games?platform=...` - Filter games
- ✅ GET `/content/games/{gameId}` - Get game details

### Content - Books (3 tests)
- ✅ GET `/content/books` - List books
- ✅ GET `/content/books?search=...` - Search books
- ✅ GET `/content/books/{bookId}` - Get book details

### Content - Locations (3 tests)
- ✅ GET `/content/locations` - List locations
- ✅ GET `/content/locations?country=...` - Filter locations
- ✅ GET `/content/locations/{locationId}` - Get location details

### Search (2 tests)
- ✅ GET `/search?query=...` - Global search
- ✅ GET `/search?query=...&categories=...` - Filtered search

### Aura Profile (3 tests)
- ✅ GET `/aura/profile` - Get current user's aura
- ✅ PUT `/aura/profile` - Update aura profile
- ✅ GET `/aura/profile/{userId}` - Get user's aura by ID

### Shares (2 tests)
- ✅ POST `/aura/shares` - Create new share
- ✅ GET `/aura/shares` - Get user's shares

**Total: 30+ test cases**

## 🚀 Quick Start

### Installation

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Or install manually
pip install pytest requests pytest-html
```

### Running Tests

#### Option 1: Standalone Script (Recommended for quick checks)

```bash
# Run with default URL (http://localhost:3000/api/v1)
python test_api.py

# Run with custom URL
python test_api.py --url http://localhost:5000/api/v1

# Run with deployed API
python test_api.py --url https://api.vibecheck.com/api/v1
```

#### Option 2: Pytest (Recommended for CI/CD)

```bash
# Run all tests with verbose output
pytest test_api.py -v

# Run with HTML report
pytest test_api.py -v --html=report.html --self-contained-html

# Run specific test
pytest test_api.py::test_login -v

# Run tests matching pattern
pytest test_api.py -k "movies" -v

# Run with JSON report
pytest test_api.py --json-report --json-report-file=report.json
```

## 📊 Output Examples

### Standalone Script Output

```
======================================================================
VibeCheck API Test Suite
======================================================================
Base URL: http://localhost:3000/api/v1
======================================================================

🏥 Health Check
----------------------------------------------------------------------
✓ PASS | Health Check | Status: 200

🔐 Authentication Tests
----------------------------------------------------------------------
✓ PASS | POST /auth/register | Status: 201
✓ PASS | POST /auth/register (duplicate check) | Status: 409
✓ PASS | POST /auth/login | Status: 200
✓ PASS | POST /auth/login (invalid credentials) | Status: 401

...

======================================================================
Test Summary
======================================================================
Total Tests: 30
Passed: 28 ✓
Failed: 2 ✗
Success Rate: 93.3%
======================================================================
```

### Pytest Output

```
test_api.py::test_health PASSED                                  [  3%]
test_api.py::test_register PASSED                                [  6%]
test_api.py::test_login PASSED                                   [ 10%]
test_api.py::test_get_movies PASSED                              [ 13%]
...

========================== 28 passed, 2 failed in 12.43s ==========================
```

## 🔧 Configuration

### Environment Variables

You can set these before running tests:

```bash
# Example: Test against staging
export BASE_URL=https://staging-api.vibecheck.com/api/v1
python test_api.py --url $BASE_URL
```

### Test Customization

Edit `test_api.py` to customize:

- Default base URL
- Test data (usernames, passwords)
- Timeout settings
- Expected response structures

## 📝 Test Structure

The test suite is organized into a class-based structure:

```python
class VibeCheckAPITester:
    def test_health()               # Health check
    def test_register()             # Auth tests
    def test_login()
    def test_get_profile()          # Profile tests
    def test_get_movies()           # Content tests
    def test_global_search()        # Search tests
    def test_get_current_user_aura() # Aura tests
    def test_create_share()         # Shares tests
```

Each test method:
1. Sends HTTP request to the endpoint
2. Validates response status code
3. Checks response structure (when applicable)
4. Logs results with ✓/✗ indicators

## 🧪 Before Running Tests

### 1. Start the Backend

```bash
cd backend
docker compose up --build

# Or without Docker
python main.py
```

### 2. Verify Backend is Running

```bash
curl http://localhost:3000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "VibeCheck API"
}
```

### 3. Ensure Database is Ready

The backend should automatically create tables on startup. Check logs for:
```
INFO: Database tables created successfully
```

## 🎯 Testing Strategies

### Smoke Testing
Quick validation that the API is up and functioning:
```bash
python test_api.py
```

### Integration Testing
Full test suite with detailed reporting:
```bash
pytest test_api.py -v --html=report.html
```

### Continuous Integration
Add to your CI/CD pipeline:
```yaml
# .github/workflows/test.yml
- name: Run API Tests
  run: |
    pip install -r test_requirements.txt
    pytest test_api.py -v --json-report
```

### Load Testing
For performance testing, consider using:
- Apache JMeter
- Locust
- k6

## 🐛 Troubleshooting

### Connection Refused
```
Error: Connection refused
```
**Solution**: Ensure backend is running on the correct port

### 401 Unauthorized
```
✗ FAIL | GET /users/profile | Status: 401
```
**Solution**: Check JWT token generation in login/register

### 404 Not Found
```
✗ FAIL | GET /content/movies/{movieId} | Status: 404
```
**Solution**: Ensure external API integrations are working

### Timeout Errors
```
Error: Request timeout
```
**Solution**: Increase timeout in requests or check external API response times

## 📈 Advanced Usage

### Custom Test Scenarios

```python
# Create custom test scenario
tester = VibeCheckAPITester()
tester.test_register()
tester.test_login()
tester.test_create_share()
tester.test_get_user_shares()
```

### Test Specific Endpoints

```python
# Test only content endpoints
tester = VibeCheckAPITester()
tester.test_get_movies()
tester.test_get_albums()
tester.test_get_games()
tester.test_get_books()
tester.test_get_locations()
```

### Parallel Testing with pytest-xdist

```bash
pip install pytest-xdist
pytest test_api.py -n 4  # Run with 4 workers
```

## 📦 Integration with Other Tools

### Postman Import
Generate Postman collection from OpenAPI spec:
```bash
# Use openapi-to-postman converter
npm install -g openapi-to-postmanv2
openapi2postmanv2 -s openapi-mvp.yaml -o postman_collection.json
```

### cURL Examples
Convert tests to cURL commands for debugging:
```bash
# Register
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"Test123!"}'

# Login
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}'
```

## 🔐 Security Considerations

- Test data uses random strings to avoid conflicts
- Passwords are test-only (not production passwords)
- Tokens are temporary and session-specific
- No sensitive data is logged

## 📚 Additional Resources

- [OpenAPI Specification](../openapi-mvp.yaml)
- [Backend Documentation](README.md)
- [pytest Documentation](https://docs.pytest.org/)
- [requests Documentation](https://requests.readthedocs.io/)

## 🤝 Contributing

To add new tests:

1. Add test method to `VibeCheckAPITester` class
2. Call it from `run_all_tests()` method
3. Add corresponding pytest function
4. Update this README

Example:
```python
def test_new_endpoint(self):
    """Test description"""
    try:
        response = requests.get(f"{self.base_url}/new/endpoint")
        passed = response.status_code == 200
        self._log_test("GET /new/endpoint", passed, response)
        return passed
    except Exception as e:
        self._log_test("GET /new/endpoint", False, error=e)
        return False
```

## 📄 License

MIT License - Same as VibeCheck project
