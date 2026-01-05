@echo off
REM llut.bat - Windows batch wrapper for LLUT scripts
REM This script provides Windows-native commands that call the Bash scripts

setlocal enabledelayedexpansion

REM Check if Git Bash is available
where bash >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Git Bash not found!
    echo Please install Git for Windows from: https://git-scm.com/download/win
    echo Or use WSL to run these scripts.
    exit /b 1
)

REM Get the command
set COMMAND=%1

if "%COMMAND%"=="" (
    goto :help
)

if "%COMMAND%"=="help" goto :help
if "%COMMAND%"=="install" goto :install
if "%COMMAND%"=="dev" goto :dev
if "%COMMAND%"=="build" goto :build
if "%COMMAND%"=="start" goto :start
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="reset" goto :reset
if "%COMMAND%"=="test" goto :test

echo Unknown command: %COMMAND%
goto :help

:help
echo.
echo LLUT - Local Law Update Tracker
echo ================================
echo.
echo Available commands:
echo   llut help       - Show this help message
echo   llut install    - Install all dependencies
echo   llut dev        - Start development servers
echo   llut build      - Build the desktop application
echo   llut start      - Start the built application
echo   llut stop       - Stop all running processes
echo   llut clean      - Clean temporary files
echo   llut reset      - Reset local database
echo   llut test       - Run tests
echo.
goto :eof

:install
echo Installing dependencies...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..\apps\desktop
call npm install
cd ..\..
echo Installation complete!
goto :eof

:dev
echo Starting development environment...
bash scripts/dev_run.sh
goto :eof

:build
echo Building desktop application...
bash scripts/build_desktop.sh
goto :eof

:start
echo Starting application...
bash scripts/start_app.sh
goto :eof

:stop
echo Stopping all processes...
bash scripts/stop_all.sh
goto :eof

:clean
echo Cleaning temporary files...
bash scripts/cleanup.sh
goto :eof

:reset
echo Resetting database...
bash scripts/reset_db.sh
goto :eof

:test
echo Running tests...
cd backend
call venv\Scripts\activate.bat
pytest tests/
cd ..
goto :eof
