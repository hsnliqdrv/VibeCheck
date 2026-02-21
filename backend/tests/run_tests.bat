@echo off
REM Windows batch script to run API tests

echo ========================================
echo VibeCheck API Test Runner
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if backend is running
echo Checking if backend is running...
curl -s http://localhost:3000/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo.
    echo Warning: Backend doesn't seem to be running on http://localhost:3000
    echo Please start the backend first with: docker compose up
    echo.
    pause
    exit /b 1
)

echo Backend is running!
echo.

REM Install dependencies if needed
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/updating test dependencies...
pip install -q -r test_requirements.txt

echo.
echo ========================================
echo Running Tests
echo ========================================
echo.

REM Run the test based on argument
if "%1"=="smoke" (
    echo Running smoke tests...
    python smoke_test.py
) else if "%1"=="pytest" (
    echo Running pytest...
    pytest test_api.py -v --html=test_report.html --self-contained-html
    echo.
    echo Report generated: test_report.html
) else if "%1"=="quick" (
    echo Running quick validation...
    python test_api.py
) else (
    REM Default: run full test suite
    echo Running full test suite...
    python test_api.py
)

echo.
echo ========================================
echo Tests Complete
echo ========================================

pause
