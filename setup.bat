@echo off
REM GAO-Dev Setup Script for Windows
REM This script sets up the GAO-Dev development environment using uv

echo.
echo ========================================
echo GAO-Dev Environment Setup
echo ========================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] uv is not installed!
    echo.
    echo Please install uv first:
    echo   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo Or visit: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

echo [OK] Found uv
echo.

REM Sync dependencies
echo [1/3] Syncing dependencies...
uv sync
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to sync dependencies
    exit /b 1
)
echo [OK] Dependencies synced
echo.

REM Install package in development mode
echo [2/3] Installing gao-dev in development mode...
uv pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install gao-dev
    exit /b 1
)
echo [OK] gao-dev installed
echo.

REM Run health check
echo [3/3] Running health check...
uv run gao-dev version
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Activate the environment: .venv\Scripts\activate
echo   2. Run: gao-dev --help
echo   3. Initialize a project: gao-dev init --name "My Project"
echo.
