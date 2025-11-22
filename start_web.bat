@echo off
REM ============================================================================
REM GAO-Dev Web App Startup Script
REM ============================================================================
REM This script starts both the backend (Python/FastAPI) and frontend (Vite).
REM It respects environment variables from .env file for configuration.
REM
REM Environment Variables (from .env):
REM   WEB_PORT - Backend port (default: 3000)
REM   WEB_HOST - Backend host (default: 127.0.0.1)
REM   WEB_AUTO_OPEN_BROWSER - Auto-open browser (default: true)
REM
REM Usage:
REM   start_web.bat           - Start with defaults
REM   start_web.bat --no-kill - Start without killing existing processes
REM ============================================================================

setlocal enabledelayedexpansion

REM Check for --no-kill flag
set KILL_EXISTING=1
if "%1"=="--no-kill" set KILL_EXISTING=0

REM Load .env file if it exists
if exist .env (
    echo Loading configuration from .env...
    for /f "tokens=1,* delims==" %%a in ('type .env ^| findstr /v "^#" ^| findstr /v "^$"') do (
        set "%%a=%%b"
    )
)

REM Set defaults if not in environment
if "%WEB_PORT%"=="" set WEB_PORT=3000
if "%WEB_HOST%"=="" set WEB_HOST=127.0.0.1
if "%WEB_AUTO_OPEN_BROWSER%"=="" set WEB_AUTO_OPEN_BROWSER=true

REM Kill existing processes if requested
if "%KILL_EXISTING%"=="1" (
    echo Stopping any existing web server processes on ports %WEB_PORT% and 5173...
    REM Kill process on backend port
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%WEB_PORT%') do (
        taskkill /PID %%a /F 2>nul
    )
    REM Kill process on common Vite ports (5173-5180)
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
        taskkill /PID %%a /F 2>nul
    )
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5174') do (
        taskkill /PID %%a /F 2>nul
    )
    timeout /t 2 /nobreak >nul
)

echo.
echo ============================================================================
echo Starting GAO-Dev Web Application
echo ============================================================================
echo.
echo Configuration:
echo   Backend: %WEB_HOST%:%WEB_PORT%
echo   Frontend: Auto-detect (typically port 5173-5180)
echo   Auto-open browser: %WEB_AUTO_OPEN_BROWSER%
echo.
echo ============================================================================
echo.

REM Start backend in a new window
echo Starting backend server...
start "GAO-Dev Backend" cmd /k "python -m uvicorn gao_dev.web.server:app --host %WEB_HOST% --port %WEB_PORT% --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo Starting frontend dev server...
cd gao_dev\web\frontend
start "GAO-Dev Frontend" cmd /k "npm run dev"
cd ..\..\..

echo.
echo ============================================================================
echo Startup Complete!
echo ============================================================================
echo.
echo Backend: http://%WEB_HOST%:%WEB_PORT%
echo Frontend: Check the "GAO-Dev Frontend" window for the actual port
echo.
echo Both servers are running in separate windows.
echo Close those windows or press Ctrl+C to stop the servers.
echo.
echo TIP: To change ports, edit the .env file or set environment variables:
echo      set WEB_PORT=3001
echo      start_web.bat
echo.
echo You can close this window now.
echo ============================================================================
pause
