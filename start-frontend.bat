@echo off
REM Start LLUT Frontend (React + Vite)

echo ============================================================
echo Starting LLUT Frontend
echo ============================================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

REM Check if npm is installed
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not installed!
    echo Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo Node.js version:
node --version
echo.
echo npm version:
npm --version
echo.

REM Navigate to frontend directory
cd apps\desktop

REM Check if node_modules exists
if not exist "node_modules\" (
    echo [WARN] node_modules not found. Installing dependencies...
    echo.
    npm install
    echo.
)

echo Starting Vite dev server...
echo Frontend will be available at: http://localhost:1420/
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the dev server
npm run dev

REM This line will only execute if npm run dev exits
echo.
echo Frontend server stopped.
pause
