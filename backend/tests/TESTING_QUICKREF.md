# VibeCheck API Testing - Quick Reference

## 🚀 Quick Start

```bash
# 1. Start backend
docker compose up --build

# 2. Install test dependencies
pip install -r test_requirements.txt

# 3. Run tests
python test_api.py
```

## 📋 Test Commands

### Simple Testing
```bash
python test_api.py                    # Full test suite (standalone)
python smoke_test.py                  # Quick smoke test
python test_examples.py 3             # Run example #3 (user journey)
```

### With Pytest
```bash
pytest test_api.py -v                 # Verbose output
pytest test_api.py -v --html=report.html    # Generate HTML report
pytest test_api.py -k "movies"        # Run only movie tests
pytest test_api.py::test_login        # Run specific test
```

### Windows Shortcuts
```cmd
run_tests.bat              # Full test suite
run_tests.bat smoke        # Smoke tests only
run_tests.bat pytest       # Pytest with HTML report
```

### Linux/Mac Shortcuts
```bash
chmod +x run_tests.sh      # Make executable (first time)
./run_tests.sh             # Full test suite  
./run_tests.sh smoke       # Smoke tests only
./run_tests.sh pytest      # Pytest with HTML report
```

## 🎯 What Each Script Does

| Script | Purpose | Use Case |
|--------|---------|----------|
| `test_api.py` | Full test suite | Complete API validation |
| `smoke_test.py` | Quick health check | Fast validation |
| `test_examples.py` | Usage examples | Learning & custom scenarios |
| `run_tests.bat/sh` | Automated runner | Easy execution |

## 📊 Test Coverage

### ✅ Covered Endpoints (30+ tests)

**Auth (4 tests)**
- POST /auth/register
- POST /auth/login

**User Profile (3 tests)**
- GET/PUT /users/profile
- GET /users/{userId}

**Content (15 tests)**
- Movies: GET /content/movies, GET /content/movies/{id}
- Albums: GET /content/albums, GET /content/albums/{id}
- Games: GET /content/games, GET /content/games/{id}
- Books: GET /content/books, GET /content/books/{id}
- Locations: GET /content/locations, GET /content/locations/{id}

**Search (2 tests)**
- GET /search

**Aura (3 tests)**
- GET/PUT /aura/profile
- GET /aura/profile/{userId}

**Shares (2 tests)**
- GET/POST /aura/shares

## 🔧 Common Options

### Custom API URL
```bash
python test_api.py --url http://localhost:5000/api/v1
python test_api.py --url https://staging.api.com/api/v1
```

### Pytest Filters
```bash
pytest -k "auth"           # Run auth tests
pytest -k "content"        # Run content tests
pytest -k "not aura"       # Skip aura tests
pytest -v --tb=short       # Short traceback
pytest --lf                # Run last failed
```

## 🐛 Troubleshooting

### Backend not running
```
Error: Connection refused
```
**Fix:** `docker compose up`

### Missing dependencies
```
ModuleNotFoundError: No module named 'requests'
```
**Fix:** `pip install -r test_requirements.txt`

### Port conflict
```
Error: Address already in use
```
**Fix:** Change port in docker-compose.yml or stop conflicting service

### Auth failures
```
✗ FAIL | GET /users/profile | Status: 401
```
**Fix:** Check JWT_SECRET_KEY in .env matches between tests and backend

## 📈 Output Interpretation

### Success
```
✓ PASS | POST /auth/login | Status: 200
```
✅ Endpoint working correctly

### Expected Failure
```
✓ PASS | POST /auth/login (invalid credentials) | Status: 401
```
✅ Proper error handling

### Actual Failure
```
✗ FAIL | GET /content/movies | Status: 500
```
❌ Server error - check logs

## 🎨 Example Workflows

### Pre-deployment Check
```bash
python smoke_test.py && python test_api.py
```

### Development Testing
```bash
pytest test_api.py -v --tb=short
```

### CI/CD Pipeline
```bash
pytest test_api.py --json-report --json-report-file=results.json
```

### Performance Check
```bash
python test_examples.py 7
```

## 📦 Files Created

```
backend/
├── test_api.py              # Main test suite
├── smoke_test.py            # Quick validation
├── test_examples.py         # Usage examples
├── test_requirements.txt    # Test dependencies
├── pytest.ini               # Pytest config
├── run_tests.bat            # Windows runner
├── run_tests.sh             # Linux/Mac runner
├── TEST_README.md           # Detailed documentation
└── TESTING_QUICKREF.md      # This file
```

## 🔗 Links

- Full Documentation: [TEST_README.md](TEST_README.md)
- OpenAPI Spec: [openapi-mvp.yaml](../openapi-mvp.yaml)
- Backend README: [README.md](README.md)

## 💡 Tips

1. **Run smoke test first** - Catches basic issues quickly
2. **Use pytest for CI/CD** - Better reporting & integration
3. **Check HTML reports** - Easier to read than terminal output
4. **Test examples** - Learn by running examples
5. **Custom scenarios** - Import VibeCheckAPITester class for custom tests

## 🎯 Next Steps

1. Run smoke test: `python smoke_test.py`
2. Run full suite: `python test_api.py`
3. Generate report: `pytest test_api.py --html=report.html`
4. Check report: Open `test_report.html` in browser
5. Learn more: `python test_examples.py`

---

**Need help?** Check [TEST_README.md](TEST_README.md) for detailed documentation.
