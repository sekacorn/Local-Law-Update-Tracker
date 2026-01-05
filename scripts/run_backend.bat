@echo off
REM Backend startup script for LLUT
REM Starts the FastAPI backend server

echo Starting LLUT Backend...

REM Get the script directory
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%..\backend

REM Change to backend directory
cd /d "%BACKEND_DIR%"

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

REM Run the backend
echo Backend starting on http://localhost:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
