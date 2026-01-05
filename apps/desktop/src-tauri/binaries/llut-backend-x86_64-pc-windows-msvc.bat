@echo off
REM LLUT Backend Sidecar Wrapper for Windows
REM This script is executed by Tauri as a sidecar process

REM Get the Tauri resources directory
set RESOURCE_DIR=%~dp0..\..\

REM Start the backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir "%RESOURCE_DIR%"
