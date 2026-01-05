@echo off
REM Stop LLUT Frontend and Clean Up Memory

echo ============================================================
echo Stopping LLUT Frontend
echo ============================================================
echo.

REM Find and kill all Node.js processes running on port 1420
echo Searching for Node processes on port 1420...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :1420 ^| findstr LISTENING') do (
    echo Found process with PID: %%a
    taskkill /F /PID %%a >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Stopped process %%a
    )
)

REM Kill any Vite processes
echo.
echo Stopping Vite processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq vite*" >nul 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Vite*" >nul 2>nul

REM More aggressive: kill all node processes (use with caution)
REM Uncomment the next line if you want to kill ALL Node processes
REM taskkill /F /IM node.exe >nul 2>nul

echo.
echo Cleaning up cache and temporary files...

REM Clean Vite cache
if exist "apps\desktop\node_modules\.vite\" (
    echo Removing Vite cache...
    rmdir /s /q "apps\desktop\node_modules\.vite" >nul 2>nul
    echo [OK] Vite cache cleared
)

REM Clean dist folder
if exist "apps\desktop\dist\" (
    echo Removing dist folder...
    rmdir /s /q "apps\desktop\dist" >nul 2>nul
    echo [OK] Dist folder cleared
)

REM Clean npm cache (optional - uncomment if needed)
REM echo Cleaning npm cache...
REM npm cache clean --force

REM Delete .frontend.pid file if it exists
if exist ".frontend.pid" (
    echo Removing .frontend.pid...
    del /q ".frontend.pid" >nul 2>nul
)

echo.
echo ============================================================
echo Frontend stopped and cleaned up!
echo ============================================================
echo.
echo Memory cleanup completed:
echo   - Killed Node processes on port 1420
echo   - Removed Vite cache
echo   - Removed build artifacts
echo.

pause
