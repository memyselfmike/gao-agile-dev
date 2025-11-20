#!/bin/bash
# Comprehensive cleanup and reinstall script for GAO-Dev development
# This fixes stale site-packages issues and ensures true editable mode

set -e  # Exit on error

echo "========================================"
echo "GAO-Dev Development Reinstall Script"
echo "========================================"
echo ""
echo "This will:"
echo "1. Uninstall all gao-dev packages"
echo "2. Clean up all cache and stale files"
echo "3. Reinstall in proper editable mode"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "[1/5] Uninstalling gao-dev..."
pip uninstall -y gao-dev || true

echo ""
echo "[2/5] Cleaning global site-packages..."
# Find Python site-packages directories
for site_dir in /usr/local/lib/python*/site-packages ~/.local/lib/python*/site-packages; do
    if [ -d "$site_dir/gao_dev" ]; then
        echo "  Removing $site_dir/gao_dev"
        rm -rf "$site_dir/gao_dev"
    fi
    if compgen -G "$site_dir/gao_dev-*.dist-info" > /dev/null; then
        echo "  Removing gao_dev dist-info directories in $site_dir"
        rm -rf "$site_dir"/gao_dev-*.dist-info
    fi
done

echo ""
echo "[3/5] Cleaning Python bytecode cache..."
if [ -d "gao_dev" ]; then
    echo "  Removing __pycache__ directories..."
    find gao_dev -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
fi

if [ -d "gao_dev.egg-info" ]; then
    echo "  Removing gao_dev.egg-info..."
    rm -rf gao_dev.egg-info
fi

if [ -d "build" ]; then
    echo "  Removing build directory..."
    rm -rf build
fi

if [ -d "dist" ]; then
    echo "  Removing dist directory..."
    rm -rf dist
fi

echo ""
echo "[4/5] Reinstalling in editable mode..."
pip install -e .

echo ""
echo "========================================"
echo "Verifying installation..."
echo "========================================"
python -c "import gao_dev; print('[OK] gao_dev location:', gao_dev.__file__)"
pip show gao-dev

echo ""
echo "========================================"
echo "Done! Your development environment is clean."
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Close all terminal windows"
echo "2. Open a fresh terminal"
echo "3. Run: gao-dev start"
echo ""
echo "To verify: python verify_install.py"
echo ""
