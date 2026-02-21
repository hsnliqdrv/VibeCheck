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

# Check if backend is running
echo "Checking if backend is running..."
if ! curl -s http://localhost:3000/api/v1/health > /dev/null 2>&1; then
    echo ""
    echo "Warning: Backend doesn't seem to be running on http://localhost:3000"
    echo "Please start the backend first with: docker compose up"
    echo ""
    exit 1
fi

echo "Backend is running!"
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

echo ""
echo "========================================"
echo "Running Tests"
echo "========================================"
echo ""

# Run the test based on argument
case "$1" in
    smoke)
        echo "Running smoke tests..."
        python3 smoke_test.py
        ;;
    pytest)
        echo "Running pytest..."
        pytest test_api.py -v --html=test_report.html --self-contained-html
        echo ""
        echo "Report generated: test_report.html"
        ;;
    quick)
        echo "Running quick validation..."
        python3 test_api.py
        ;;
    *)
        # Default: run full test suite
        echo "Running full test suite..."
        python3 test_api.py
        ;;
esac

echo ""
echo "========================================"
echo "Tests Complete"
echo "========================================"
