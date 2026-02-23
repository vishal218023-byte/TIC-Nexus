@echo off
cd /d %~dp0
chcp 65001 > nul
title TIC Nexus - Production Server
color 0A

echo ========================================
echo  TIC Nexus - Production Server
echo  Starting Application...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run run_nexus.bat first to create it
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check dependencies
echo Checking dependencies...
pip show uvicorn >nul 2>&1
if errorlevel 1 (
    echo Installing uvicorn...
    pip install uvicorn --quiet
)

REM Check if static assets exist
if not exist "static\css\tailwind.css" (
    echo.
    echo WARNING: Static assets not found!
    echo Please run 'python scripts\download_assets.py' to download required files.
    echo.
)

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Using default settings. For production, create a .env file with:
    echo   SECRET_KEY=your-secret-key
    echo   DEBUG=False
    echo.
)

echo.
echo ========================================
echo  Starting TIC Nexus Production Server...
echo ========================================
echo.
echo Server will be available at:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo.
echo IMPORTANT: Running in PRODUCTION mode
echo   - Debug: OFF
echo   - Reload: OFF
echo   - Using Uvicorn ASGI server
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Set production environment variables
set DEBUG=False

REM Start the application with Uvicorn (ASGI server)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
