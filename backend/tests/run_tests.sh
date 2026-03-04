#!/bin/bash
# Shell script to run API tests (Linux/Mac)

set -e

echo "========================================"
echo "VibeCheck API Test Runner"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

echo ""

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/updating test dependencies..."
pip install -q -r test_requirements.txt
if [ -f "../requirements.txt" ]; then
    echo "Installing backend dependencies..."
    pip install -q -r ../requirements.txt
fi

echo ""
echo "========================================"
# Always run unit tests (Flask test client — no server needed)
echo "Running Unit Tests (no server required)"
echo "========================================"
echo ""

pytest -v -m "not integration" --html=test_report.html --self-contained-html
UNIT_EXIT=$?

echo ""

# Run integration tests only if the backend is reachable
echo "========================================"
echo "Checking if backend is available for integration tests..."
if curl -s http://localhost:3000/api/v1/health > /dev/null 2>&1; then
    echo "Backend is running — running integration tests"
    echo "========================================"
    echo ""
    pytest -v -m integration --html=test_report_integration.html --self-contained-html
    INTEG_EXIT=$?
else
    echo "Backend is not running — skipping integration tests"
    echo "Start the backend with: docker compose up"
    INTEG_EXIT=0
fi

echo ""
echo "========================================"
echo "Tests Complete."
echo "  Unit test report:        test_report.html"
if [ -f test_report_integration.html ]; then
    echo "  Integration test report: test_report_integration.html"
fi
echo "========================================"

# Exit with failure if either suite failed
if [ $UNIT_EXIT -ne 0 ] || [ $INTEG_EXIT -ne 0 ]; then
    exit 1
fi
