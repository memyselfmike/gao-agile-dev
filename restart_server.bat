@echo off
REM ============================================================================
REM GAO-Dev Web Server Restart Script
REM ============================================================================
REM This script stops all Python processes and restarts the backend server.
REM It respects environment variables from .env file for port configuration.
REM
REM Environment Variables (from .env):
REM   WEB_PORT - Backend port (default: 3000)
REM   WEB_HOST - Backend host (default: 127.0.0.1)
REM ============================================================================

REM Load .env file if it exists (basic implementation)
if exist .env (
    echo Loading configuration from .env...
    for /f "tokens=1,* delims==" %%a in ('type .env ^| findstr /v "^#" ^| findstr /v "^$"') do (
        set "%%a=%%b"
    )
)

REM Use environment variable or default to 3000
if "%WEB_PORT%"=="" set WEB_PORT=3000
if "%WEB_HOST%"=="" set WEB_HOST=127.0.0.1

echo Stopping backend server on port %WEB_PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%WEB_PORT%') do (
    taskkill /PID %%a /F 2>nul
)
timeout /t 2 /nobreak >nul

echo Starting backend server on %WEB_HOST%:%WEB_PORT%...
start "Backend Server" cmd /k "python -m uvicorn gao_dev.web.server:app --host %WEB_HOST% --port %WEB_PORT% --reload"

echo Backend server restarting in new window...
echo.
echo Configuration:
echo   Host: %WEB_HOST%
echo   Port: %WEB_PORT%
echo.
echo You can close this window now.
