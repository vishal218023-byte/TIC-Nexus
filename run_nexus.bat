@echo off
chcp 65001 > nul
title TIC Nexus - BEL Technical Literature Center
color 0A

echo ========================================
echo  TIC Nexus - BEL Library System
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
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Check if static assets exist
if not exist "static\css\tailwind.css" (
    echo.
    echo WARNING: Static assets not found!
    echo Please run 'python download_assets.py' to download required files.
    echo The application will not work properly without these assets.
    echo.
    pause
)

echo.
echo ========================================
echo  Starting TIC Nexus Server...
echo ========================================
echo.
echo Server will be available at:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo.
echo Default credentials:
echo   Username: admin
echo   Password: admin123
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the application with Uvicorn (ASGI server for FastAPI)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
