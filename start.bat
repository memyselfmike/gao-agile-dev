@echo off
REM GAO-Dev Start Script for Windows
REM This script ensures the environment is set up and launches gao-dev

echo.
echo ========================================
echo GAO-Dev Startup
echo ========================================
echo.

REM Check if we're in the project root
if not exist "pyproject.toml" (
    echo [ERROR] Not in gao-agile-dev project root!
    echo Please cd to the project directory first.
    exit /b 1
)

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] uv is not installed!
    echo.
    echo Install uv first:
    echo   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    exit /b 1
)

echo [OK] Found uv
echo.

REM Check if .venv exists, create if not
if not exist ".venv" (
    echo [INFO] Virtual environment not found, creating...
    uv venv
    echo [OK] Virtual environment created
    echo.
)

REM Sync dependencies
echo [INFO] Syncing dependencies...
uv sync
echo [OK] Dependencies synced
echo.

REM Install package in editable mode
echo [INFO] Installing gao-dev...
uv pip install -e .
echo [OK] gao-dev installed
echo.

REM Activate the virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Show version
echo ========================================
echo Environment Ready!
echo ========================================
echo.
python -m gao_dev.cli.commands version 2>nul || echo GAO-Dev installed
echo.

REM Check for command line arguments
if "%~1"=="" (
    REM No arguments, start interactive chat
    echo Starting interactive chat...
    echo To run a specific command, use: start.bat [command]
    echo Example: start.bat --help
    echo.
    python -m gao_dev.cli.commands start
) else (
    REM Run with provided arguments
    python -m gao_dev.cli.commands %*
)
