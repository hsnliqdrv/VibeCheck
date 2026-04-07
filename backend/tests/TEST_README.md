# VibeCheck API Testing

Comprehensive test suite for the VibeCheck backend API based on the OpenAPI specification.

## 📋 Test Coverage

The test suite covers the full API surface across **270+ test cases**:

### Authentication
- POST `/auth/register` — User registration + duplicate email validation
- POST `/auth/login` — Login + invalid credentials check
- Email verification flow (register → verify → login gating)
- Forgot password / reset password flow

### User Profile
- GET `/users/profile` — Get current user profile
- PUT `/users/profile` — Update user profile (including `socialMediaLinks` validation)
- GET `/users/{userId}` — Get user by ID

### Content (Movies, Albums, Games, Books, Locations)
Each category supports:
- `GET /content/{category}` — List items
- `GET /content/{category}?search=...` — Search / filter
- `GET /content/{category}/{id}` — Get item details

### Search
- GET `/search?query=...` — Global search
- GET `/search?query=...&categories=...` — Filtered search

### Aura Profile
- GET `/aura/profile` — Get current user's aura
- PUT `/aura/profile` — Update aura profile
- GET `/aura/profile/{userId}` — Get user's aura by ID
- Aura inference — Auto-generated aesthetic tags and colors

### Shares
- POST `/aura/shares` — Create a new share
- GET `/aura/shares` — Get user's shares

### Social / Rooms
- Room CRUD (create, list, get, join, leave)
- Room posts (create, list)
- Trending rooms

### Discovery
- GET `/discovery/feed` — Discovery feed endpoint

### Gamification & Badges
- Curator levels, XP, streaks
- Badge system with rarities
- Badge date formatting

## 🏗️ Test Structure

Tests are split into two directories for easy execution:

```
backend/tests/
├── unit/                          # Fast, no Docker needed
│   └── test_new_endpoints.py      # 32 tests — Flask test client + SQLite
├── integration/                   # Requires running server + PostgreSQL
│   ├── test_api.py                # ~211 tests — Full API via VibeCheckAPITester
│   ├── test_new_features.py       # 35 tests — Aura inference & rooms
│   └── test_legacy_wrapper.py     # Pytest wrapper for test_api.py
├── pytest.ini                     # Config (warnings, logging, markers)
└── test_requirements.txt          # Test dependencies
```

### Unit Tests (`tests/unit/`)

Run with an **in-memory SQLite** database using the Flask test client. No server or Docker required.

```bash
cd backend
pytest tests/unit/
```

Run each unit file individually:

```bash
# pytest-based unit tests
pytest tests/unit/test_new_endpoints.py -v
pytest tests/unit/test_email_service.py -v
pytest tests/unit/test_seed_content.py -v

# script-style tests
python tests/unit/test_direct_upload.py
python tests/unit/test_spaces_connection.py
python tests/unit/test_upload_avatar.py
python tests/unit/test_upload_post.py
```

Optional path overrides used by unit tests:

```bash
# pytest files that import app modules
# uses BACKEND_PATH when set, otherwise current directory
BACKEND_PATH=/absolute/path/to/backend pytest tests/unit/test_email_service.py -v

# script files that load env config
# uses DOTENV_PATH when set, otherwise current directory .env
DOTENV_PATH=/absolute/path/to/.env python tests/unit/test_spaces_connection.py

# direct upload script input image
# uses TEST_FILE_PATH when set, otherwise current directory example.png
TEST_FILE_PATH=/absolute/path/to/example.png python tests/unit/test_direct_upload.py
```

**What's tested:**
- Email verification gating (register → must verify → then login)
- Forgot password / reset password flow
- `socialMediaLinks` field validation
- Badge date formatting
- Discovery feed endpoint

### Integration Tests (`tests/integration/`)

Run against a **live Flask server** backed by PostgreSQL. Requires Docker.

```bash
# Start the database
docker compose up -d db

# Optionally start the full backend
docker compose up -d

# Run
cd backend
pytest tests/integration/
```

**What's tested:**
- All 30+ OpenAPI endpoints (auth, content, search, aura, shares, social)
- Aura inference (auto aesthetic tags and colors)
- Aesthetic rooms (CRUD, join/leave, posts)

## 🚀 Running Tests

```bash
# Run everything
cd backend
pytest tests/

# Unit only (fast)
pytest tests/unit/

# Integration only (needs Docker)
pytest tests/integration/

# Verbose
pytest tests/unit/ -v

# Single file
pytest tests/unit/test_new_endpoints.py -v

# Single test
pytest tests/unit/test_new_endpoints.py::test_forgot_password -v

# Pattern match
pytest tests/ -k "auth"

# Re-run last failed
pytest tests/ --lf
```

## 🔧 Configuration

### pytest.ini

Located at `tests/pytest.ini`, pre-configured to:
- **Suppress warnings**: `DeprecationWarning` filtered out (handles `datetime.utcnow()` on Python 3.12+)
- **Silence logs**: `log_cli = false` prevents SQLAlchemy from flooding test output
- **Strict markers**: Enforces declared markers only
- **Short tracebacks**: Cleaner failure output

### Environment

`python-dotenv` is installed in the backend, so running `pytest` locally will automatically load variables from your `.env` file — the same file Docker uses.

### Test Dependencies

```bash
pip install -r tests/test_requirements.txt
```

Contents:
- `pytest` — Test framework
- `requests` — HTTP client for integration tests
- `pytest-html` — HTML report generation
- `pytest-json-report` — JSON report generation

## 🐛 Troubleshooting

### Connection Refused
```
Error: Connection refused
```
**Fix:** Start the backend — `docker compose up -d`

### Missing Dependencies
```
ModuleNotFoundError: No module named 'requests'
```
**Fix:** `pip install -r tests/test_requirements.txt`

### 401 Unauthorized
```
✗ FAIL | GET /users/profile | Status: 401
```
**Fix:** Ensure `JWT_SECRET_KEY` in `.env` is consistent between app and tests

### Noisy Log Output
Already handled by `pytest.ini` configuration. If you still see noise, verify `log_cli = false` is set.

## 🧪 Before Running Integration Tests

1. **Start the backend:**
   ```bash
   cd backend
   docker compose up --build -d
   ```

2. **Verify it's running:**
   ```bash
   curl http://localhost:3000/api/v1/health
   ```
   Expected: `{"status": "healthy", "service": "VibeCheck API"}`

3. **Run:**
   ```bash
   pytest tests/integration/ -v
   ```

## 📈 Advanced Usage

### Generate HTML Report
```bash
pytest tests/ -v --html=tests/test_report.html --self-contained-html
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
- name: Run Unit Tests
  run: |
    pip install -r tests/test_requirements.txt
    cd backend
    pytest tests/unit/ -v
```

### Custom Test Scenarios (Integration)

The `VibeCheckAPITester` class in `test_api.py` can be imported for ad-hoc testing:

```python
from tests.integration.test_api import VibeCheckAPITester

tester = VibeCheckAPITester()
tester.test_register()
tester.test_login()
tester.test_get_movies()
```

## 🔗 Resources

- Quick reference: [TESTING_QUICKREF.md](TESTING_QUICKREF.md)
- OpenAPI specification: [openapi-mvp.yaml](../../openapi-mvp.yaml)
- Backend documentation: [../README.md](../README.md)
- Swagger UI (live): http://localhost:3000/docs
