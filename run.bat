@echo off
REM run.bat - Simple Windows runner for LLUT
REM Handles dependency installation better on Windows

echo ========================================
echo LLUT - Local Law Update Tracker
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3.11+ is required but not found
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Show Python version
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Using Python %PYVER%

REM Navigate to backend
cd /d "%~dp0backend"

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo.
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip using python -m pip (avoids Windows locking issues)
echo.
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel --quiet

REM Install minimal dependencies one by one (more reliable on Windows)
echo.
echo Installing dependencies (this may take a few minutes)...
echo.

echo [1/10] Installing FastAPI...
python -m pip install fastapi==0.109.0 --quiet
if %errorlevel% neq 0 goto :install_error

echo [2/10] Installing Uvicorn...
python -m pip install uvicorn==0.27.0 --quiet
if %errorlevel% neq 0 goto :install_error

echo [3/10] Installing Pydantic...
python -m pip install pydantic==2.5.3 --quiet
if %errorlevel% neq 0 goto :install_error

echo [4/10] Installing Pydantic Settings...
python -m pip install pydantic-settings==2.1.0 --quiet
if %errorlevel% neq 0 goto :install_error

echo [5/10] Installing aiosqlite...
python -m pip install aiosqlite==0.19.0 --quiet
if %errorlevel% neq 0 goto :install_error

echo [6/10] Installing httpx...
python -m pip install httpx==0.26.0 --quiet
if %errorlevel% neq 0 goto :install_error

echo [7/10] Installing BeautifulSoup4...
python -m pip install beautifulsoup4==4.12.3 --quiet
if %errorlevel% neq 0 goto :install_error

echo [8/10] Installing python-dateutil...
python -m pip install python-dateutil==2.8.2 --quiet
if %errorlevel% neq 0 goto :install_error

echo [9/10] Installing python-dotenv...
python -m pip install python-dotenv==1.0.0 --quiet
if %errorlevel% neq 0 goto :install_error

echo [10/10] Installation complete!
echo.

REM Create app_data directory
cd /d "%~dp0"
if not exist "app_data" mkdir app_data
if not exist "app_data\cache" mkdir app_data\cache

REM Start the backend
echo.
echo ========================================
echo Starting LLUT Backend...
echo ========================================
echo.
echo Backend will run at: http://localhost:8000
echo API Docs at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0backend"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

goto :eof

:install_error
echo.
echo Error: Failed to install dependencies
echo Please check your internet connection and try again
pause
exit /b 1
