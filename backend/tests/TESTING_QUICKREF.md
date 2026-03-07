# VibeCheck API Testing - Quick Reference

## 🚀 Quick Start

```bash
# Install test dependencies
pip install -r tests/test_requirements.txt

# Run unit tests (fast, no Docker needed)
cd backend
pytest tests/unit/

# Run integration tests (requires Docker + PostgreSQL)
docker compose up -d db
pytest tests/integration/
```

## 📋 Test Structure

Tests are organized into two directories — no `-m` markers needed:

| Directory | What it tests | Database | Requires Docker? |
|-----------|--------------|----------|-------------------|
| `tests/unit/` | Endpoint logic, validation, flows | In-memory SQLite | No |
| `tests/integration/` | Full API against running server | PostgreSQL | Yes |

### Unit Tests (`tests/unit/`)
- **test_new_endpoints.py** — Email verification, forgot/reset password, social media links validation, badge formatting, discovery feed (32 tests, Flask test client)

### Integration Tests (`tests/integration/`)
- **test_api.py** — Comprehensive API coverage via `VibeCheckAPITester` class against a running server (~211 tests)
- **test_new_features.py** — Aura inference, aesthetic rooms CRUD, room posts (35 pytest tests)
- **test_legacy_wrapper.py** — Pytest wrapper that runs the full `test_api.py` suite

## 📊 Test Commands

```bash
# Run all tests
pytest tests/

# Run only unit tests (fast)
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Verbose output
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_new_endpoints.py -v

# Run tests matching a pattern
pytest tests/unit/ -k "password"

# Run a single test function
pytest tests/unit/test_new_endpoints.py::test_forgot_password -v

# Short traceback on failure
pytest tests/ -v --tb=short

# Re-run only last failed
pytest tests/ --lf
```

## 🔧 Configuration

`pytest.ini` is pre-configured to:
- Suppress `DeprecationWarning` (e.g., `datetime.utcnow()` on Python 3.12+)
- Silence SQLAlchemy INFO-level log spam (`log_cli = false`)
- Use short tracebacks and strict markers

`python-dotenv` is installed, so `pytest` automatically loads your `.env` file.

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `Connection refused` | Start backend: `docker compose up -d` |
| `ModuleNotFoundError` | `pip install -r tests/test_requirements.txt` |
| `401 Unauthorized` | Check `JWT_SECRET_KEY` in `.env` |
| Noisy log output | Already handled by `pytest.ini` |

## 📦 Test Directory Layout

```
backend/tests/
├── pytest.ini                 # Pytest configuration
├── test_requirements.txt      # Test dependencies
├── unit/
│   └── test_new_endpoints.py  # Fast isolated tests (SQLite)
├── integration/
│   ├── test_api.py            # Full API test suite (requires server)
│   ├── test_new_features.py   # Aura & rooms tests (requires server)
│   └── test_legacy_wrapper.py # Pytest wrapper for test_api.py
├── TESTING_QUICKREF.md        # This file
└── TEST_README.md             # Detailed documentation
```

## 🔗 Links

- Detailed docs: [TEST_README.md](TEST_README.md)
- OpenAPI spec: [openapi-mvp.yaml](../../openapi-mvp.yaml)
- Backend README: [../README.md](../README.md)
