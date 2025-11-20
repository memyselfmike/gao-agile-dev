@echo off
REM Comprehensive cleanup and reinstall script for GAO-Dev development
REM This fixes stale site-packages issues and ensures true editable mode

echo ========================================
echo GAO-Dev Development Reinstall Script
echo ========================================
echo.
echo This will:
echo 1. Uninstall all gao-dev packages
echo 2. Clean up all cache and stale files
echo 3. Reinstall in proper editable mode
echo.
pause

echo.
echo [1/5] Uninstalling gao-dev...
pip uninstall -y gao-dev

echo.
echo [2/5] Cleaning global site-packages...
if exist "C:\Python314\Lib\site-packages\gao_dev" (
    echo Removing C:\Python314\Lib\site-packages\gao_dev
    rmdir /s /q "C:\Python314\Lib\site-packages\gao_dev"
)
if exist "C:\Python314\Lib\site-packages\gao_dev-*.dist-info" (
    echo Removing old dist-info directories...
    for /d %%G in ("C:\Python314\Lib\site-packages\gao_dev-*.dist-info") do rmdir /s /q "%%G"
)

echo.
echo [3/5] Cleaning user site-packages...
if exist "C:\Users\%USERNAME%\AppData\Roaming\Python\Python314\site-packages\gao_dev" (
    echo Removing user site gao_dev
    rmdir /s /q "C:\Users\%USERNAME%\AppData\Roaming\Python\Python314\site-packages\gao_dev"
)
if exist "C:\Users\%USERNAME%\AppData\Roaming\Python\Python314\site-packages\gao_dev-*.dist-info" (
    echo Removing user dist-info directories...
    for /d %%G in ("C:\Users\%USERNAME%\AppData\Roaming\Python\Python314\site-packages\gao_dev-*.dist-info") do rmdir /s /q "%%G"
)

echo.
echo [4/5] Cleaning Python bytecode cache...
if exist "gao_dev\__pycache__" (
    echo Removing __pycache__ directories...
    for /d /r gao_dev %%G in ("__pycache__") do @if exist "%%G" rmdir /s /q "%%G"
)

if exist "gao_dev.egg-info" (
    echo Removing gao_dev.egg-info...
    rmdir /s /q "gao_dev.egg-info"
)

if exist "build" (
    echo Removing build directory...
    rmdir /s /q "build"
)

if exist "dist" (
    echo Removing dist directory...
    rmdir /s /q "dist"
)

echo.
echo [5/5] Reinstalling in editable mode...
pip install -e .

echo.
echo ========================================
echo Verifying installation...
echo ========================================
python -c "import gao_dev; print('✓ gao_dev location:', gao_dev.__file__)"
pip show gao-dev

echo.
echo ========================================
echo Done! Your development environment is clean.
echo ========================================
echo.
echo Next steps:
echo 1. Close all terminal windows
echo 2. Open a fresh terminal
echo 3. Run: gao-dev start
echo.
pause
