@echo off
REM Workspace Cleanup Script for Windows
REM Removes test artifacts, corrupt directories, and temporary files
REM Run this before creating a release or committing changes

echo ================================================================================
echo GAO-Dev Workspace Cleanup
echo ================================================================================
echo.

REM Change to project root
cd /d "%~dp0.."

echo [1/6] Removing corrupt directories...
if exist "C:Projectsgao-agile-devtestsunitcore" rmdir /s /q "C:Projectsgao-agile-devtestsunitcore"
if exist "C:Testingscripts" rmdir /s /q "C:Testingscripts"
if exist "C:Usersmikejgao-final-test" rmdir /s /q "C:Usersmikejgao-final-test"
if exist "Projectsgao-agile-devgao_devwebfrontend" rmdir /s /q "Projectsgao-agile-devgao_devwebfrontend"
if exist "Testingvenv-beta" rmdir /s /q "Testingvenv-beta"
if exist "-p" rmdir /s /q "-p"
echo    - Done

echo [2/6] Removing test artifacts...
if exist "gao_dev.db" del /f /q "gao_dev.db"
if exist "server_output.log" del /f /q "server_output.log"
if exist "nul" del /f /q "nul"
if exist "test_output.log" del /f /q "test_output.log"
if exist "test_output.txt" del /f /q "test_output.txt"
for %%F in (=*.*.*) do del /f /q "%%F"
echo    - Done

echo [3/6] Removing Playwright artifacts...
if exist ".playwright-mcp" rmdir /s /q ".playwright-mcp"
for /r . %%F in (*.png) do (
    echo %%F | findstr /v /c:"docs" | findstr /v /c:"screenshots" >nul && del /f /q "%%F"
)
echo    - Done

echo [4/6] Removing frontend build cache...
if exist "gao_dev\web\frontend\.vite" rmdir /s /q "gao_dev\web\frontend\.vite"
echo    - Done

echo [5/6] Removing coverage reports...
if exist ".coverage" del /f /q ".coverage"
if exist "htmlcov" rmdir /s /q "htmlcov"
echo    - Done

echo [6/6] Removing test transcripts...
if exist ".gao-dev\test_transcripts" rmdir /s /q ".gao-dev\test_transcripts"
if exist "tests\e2e\debug_reports" rmdir /s /q "tests\e2e\debug_reports"
echo    - Done

echo.
echo ================================================================================
echo Cleanup Complete!
echo ================================================================================
echo.
echo Next steps:
echo   1. Run: git status
echo   2. Review changes
echo   3. Commit clean workspace
echo.
pause
