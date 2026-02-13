#!/bin/bash

# VibeCheck - Automated Test Runner with Docker
# This script starts the backend with Docker and runs all tests

set -e  # Exit on error

echo "🚀 VibeCheck Test Runner"
echo "========================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "📦 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo "On macOS: Open Docker Desktop from Applications"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if containers are already running
if docker compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Backend containers are already running${NC}"
    read -p "Do you want to restart them? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Restarting containers..."
        docker compose down
        docker compose up --build -d
    fi
else
    echo "🐳 Starting backend with Docker Compose..."
    docker compose up --build -d
fi

echo ""
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Check if backend is healthy
MAX_ATTEMPTS=12
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:3000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy!${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo -e "${RED}❌ Backend failed to start${NC}"
        echo "Showing backend logs:"
        docker compose logs backend
        exit 1
    fi
    echo "  Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting..."
    sleep 2
done

echo ""
echo "📦 Checking test dependencies..."
cd ..

# Determine which Python to use (prefer venv, fallback to system)
if [ -f ".venv/bin/python3" ]; then
    PYTHON_CMD=".venv/bin/python3"
    echo -e "${GREEN}✓ Using virtual environment Python${NC}"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo -e "${GREEN}✓ Using virtual environment Python${NC}"
else
    PYTHON_CMD="python3"
    echo -e "${YELLOW}⚠️  Using system Python (no venv found)${NC}"
fi

# Check if requests module is available, if not install dependencies
if ! $PYTHON_CMD -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Test dependencies not found. Installing...${NC}"
    $PYTHON_CMD -m pip install pytest requests pytest-html pytest-json-report --quiet
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

echo ""
echo "🧪 Running tests..."
echo "===================="
echo ""

# Ask user which tests to run
echo "Select test type:"
echo "1) Smoke test (quick - 5 seconds)"
echo "2) Full test suite (comprehensive)"
echo "3) Pytest with HTML report"
echo "4) All of the above"
echo ""
read -p "Enter choice (1-4): " CHOICE

case $CHOICE in
    1)
        echo ""
        echo "Running smoke test..."
        $PYTHON_CMD tests/smoke_test.py
        ;;
    2)
        echo ""
        echo "Running full test suite..."
        $PYTHON_CMD tests/test_api.py
        ;;
    3)
        echo ""
        echo "Running pytest with HTML report..."
        $PYTHON_CMD -m pytest tests/test_api.py -v --html=test_report.html --self-contained-html
        echo ""
        echo -e "${GREEN}✓ Report saved to: test_report.html${NC}"
        ;;
    4)
        echo ""
        echo "=== 1. Smoke Test ==="
        $PYTHON_CMD tests/smoke_test.py
        
        echo ""
        echo "=== 2. Full Test Suite ==="
        $PYTHON_CMD tests/test_api.py
        
        echo ""
        echo "=== 3. Pytest with HTML Report ==="
        $PYTHON_CMD -m pytest tests/test_api.py -v --html=test_report.html --self-contained-html
        echo ""
        echo -e "${GREEN}✓ Report saved to: test_report.html${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "===================="
echo -e "${GREEN}✅ Testing complete!${NC}"
echo ""
read -p "Do you want to stop the backend containers? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd backend
    docker compose down
    echo -e "${GREEN}✓ Backend stopped${NC}"
else
    echo "Backend is still running on http://localhost:3000"
    echo "To stop later, run: cd backend && docker compose down"
fi
