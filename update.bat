@echo off
REM GAO-Dev Update Script for Windows
REM This script updates GAO-Dev to the latest version from the repository

echo.
echo ========================================
echo GAO-Dev Update Script
echo ========================================
echo.

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Not in a git repository!
    echo Please run this script from the gao-agile-dev directory.
    exit /b 1
)

echo [OK] Git repository detected
echo.

REM Check for uncommitted changes
git diff-index --quiet HEAD --
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] You have uncommitted changes!
    echo.
    echo Your changes:
    git status --short
    echo.
    set /p CONTINUE="Continue with update? (y/N): "
    if /i not "%CONTINUE%"=="y" (
        echo Update cancelled.
        exit /b 1
    )
)

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] uv is not installed!
    echo Falling back to pip for dependency updates.
    set USE_UV=0
) else (
    echo [OK] Found uv
    set USE_UV=1
)
echo.

REM Show current version
echo Current version:
python -m gao_dev.cli.commands version 2>nul
echo.

REM Step 1: Pull latest changes
echo [1/5] Pulling latest changes from GitHub...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to pull changes from GitHub
    echo.
    echo Troubleshooting:
    echo   - Check your internet connection
    echo   - Ensure you have access to the repository
    echo   - Try: git fetch origin, then git pull origin main
    exit /b 1
)
echo [OK] Changes pulled successfully
echo.

REM Step 2: Update dependencies
echo [2/5] Updating dependencies...
if %USE_UV%==1 (
    uv sync
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to sync dependencies with uv
        exit /b 1
    )
    uv pip install -e .
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install gao-dev
        exit /b 1
    )
) else (
    pip install -e ".[dev]" --upgrade
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to update dependencies with pip
        exit /b 1
    )
)
echo [OK] Dependencies updated
echo.

REM Step 3: Run database migrations
echo [3/5] Running database migrations...
python -m gao_dev.cli.commands db status
echo.
python -m gao_dev.cli.commands db migrate
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Database migrations had issues
    echo Run 'gao-dev db status' to check migration status
) else (
    echo [OK] Migrations completed
)
echo.

REM Step 4: Check consistency
echo [4/5] Checking file-database consistency...
python -m gao_dev.cli.commands migrate consistency-check
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Consistency issues found
    echo Run 'gao-dev migrate consistency-repair' to fix them
) else (
    echo [OK] Consistency check passed
)
echo.

REM Step 5: Verify installation
echo [5/5] Verifying installation...
python -m gao_dev.cli.commands version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Installation verification failed
    exit /b 1
)
echo.

echo ========================================
echo Update Complete!
echo ========================================
echo.
echo New version:
python -m gao_dev.cli.commands version 2>nul
echo.
echo Next steps:
echo   1. Review CHANGELOG.md for changes
echo   2. Run: gao-dev health
echo   3. Test your workflows
echo.
echo If you encounter issues:
echo   - See UPDATE.md for troubleshooting
echo   - Report bugs: https://github.com/memyselfmike/gao-agile-dev/issues
echo.
